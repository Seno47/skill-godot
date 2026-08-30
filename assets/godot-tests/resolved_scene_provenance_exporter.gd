extends SceneTree

## Run from the project root with Godot 4:
## godot --headless --path . --script res://tests/resolved_scene_provenance_exporter.gd -- \
##   --root-scene res://scenes/world/OldClinicDistrict.tscn \
##   --output reports/resolved-scene-provenance.json \
##   --build-id old-clinic-map-008-v19 \
##   --export-preset "Windows Desktop"
## Add each dynamically loaded production resource that ResourceLoader cannot discover with:
##   --runtime-dependency res://path/to/resource.tres
## Add each evidence exporter/auditor input that shapes the resolved report with:
##   --tool-input environment_coverage_exporter=res://tests/environment_coverage_exporter.gd

const DIGEST_HEADER := "skill-godot-resolved-scene-closure-v1"
var _failed := false


func _initialize() -> void:
	var options := _parse_args(OS.get_cmdline_user_args())
	for required in ["root_scene", "output", "build_id", "export_preset"]:
		if not options.has(required) or String(options[required]).is_empty():
			_fail("missing --%s" % required.replace("_", "-"))
			return

	var root_scene := _canonical_res_path(String(options.root_scene))
	if _failed:
		return
	var direct := _dependencies_for(root_scene)
	var recursive := _recursive_dependencies(root_scene)
	var runtime: Array[String] = []
	for raw_path in options.runtime_dependencies:
		var path := _canonical_res_path(String(raw_path))
		if path != root_scene and not runtime.has(path):
			runtime.append(path)
	if _failed:
		return
	runtime.sort()
	var discovered := recursive.duplicate()
	for path in runtime:
		if not discovered.has(path):
			discovered.append(path)
	discovered.sort()

	var entries: Array[Dictionary] = []
	entries.append(_file_record(root_scene, "root_scene"))
	for path in discovered:
		entries.append(_file_record(path, _resource_kind(path)))
	if _failed:
		return
	entries.sort_custom(func(a: Dictionary, b: Dictionary) -> bool: return a.path < b.path)

	var exporter_path := String(get_script().resource_path)
	var tools: Array[Dictionary] = [
		_file_record(exporter_path, "exporter_script", "exporter_script"),
		_file_record("res://export_presets.cfg", "export_presets", "export_presets"),
		_file_record("res://project.godot", "project_settings", "project_settings")
	]
	if _failed:
		return
	for raw_tool in options.tool_inputs:
		var parts := String(raw_tool).split("=", false, 1)
		if parts.size() != 2 or String(parts[0]).is_empty():
			_fail("--tool-input must use role=res://path")
			return
		tools.append(_file_record(_canonical_res_path(parts[1]), String(parts[0]), String(parts[0])))
		if _failed:
			return
	tools.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		return a.role < b.role or (a.role == b.role and a.path < b.path)
	)

	var manifest := {
		"schema_version": 1,
		"manifest_id": "%s-resolved-scene" % String(options.build_id),
		"build_id": String(options.build_id),
		"source_kind": "resolved_target_scene",
		"root_scene": root_scene,
		"engine_version": Engine.get_version_info().string,
		"export_preset_selector": String(options.export_preset),
		"dependency_discovery": {
			"method": "godot_resource_loader_recursive",
			"direct_dependencies": direct,
			"recursive_dependencies": recursive,
			"runtime_dependency_paths": runtime,
			"declared_dependency_count": discovered.size()
		},
		"entries": entries,
		"toolchain_inputs": tools
	}
	manifest.closure_digest = _closure_digest(manifest)

	var output_path := String(options.output)
	if not output_path.begins_with("res://") and not output_path.begins_with("user://"):
		output_path = "res://" + output_path.trim_prefix("./")
	var output_directory := ProjectSettings.globalize_path(output_path.get_base_dir())
	var directory_error := DirAccess.make_dir_recursive_absolute(output_directory)
	if directory_error != OK:
		_fail("cannot create output directory: %s" % output_directory)
		return
	var output := FileAccess.open(output_path, FileAccess.WRITE)
	if output == null:
		_fail("cannot open output: %s" % output_path)
		return
	output.store_string(JSON.stringify(manifest, "  ") + "\n")
	output.close()
	print("[PASS] resolved-scene-provenance dependencies=%d digest=%s output=%s" % [
		discovered.size(), manifest.closure_digest, output_path
	])
	quit(0)


func _parse_args(args: PackedStringArray) -> Dictionary:
	var result := {"runtime_dependencies": [], "tool_inputs": []}
	var index := 0
	while index < args.size():
		var key := args[index]
		if key == "--runtime-dependency" and index + 1 < args.size():
			result.runtime_dependencies.append(args[index + 1])
			index += 2
			continue
		if key == "--tool-input" and index + 1 < args.size():
			result.tool_inputs.append(args[index + 1])
			index += 2
			continue
		if key.begins_with("--") and index + 1 < args.size():
			result[key.trim_prefix("--").replace("-", "_")] = args[index + 1]
			index += 2
			continue
		index += 1
	return result


func _canonical_res_path(path: String) -> String:
	if not path.begins_with("res://"):
		_fail("dependency path must use res://: %s" % path)
		return ""
	var normalized := path.replace("\\", "/").simplify_path()
	if not normalized.begins_with("res://"):
		_fail("dependency path escapes res://: %s" % path)
		return ""
	return normalized


func _dependency_path(raw: String) -> String:
	if raw.contains("::"):
		return _canonical_res_path(raw.get_slice("::", 2))
	return _canonical_res_path(raw)


func _dependencies_for(path: String) -> Array[String]:
	var result: Array[String] = []
	for raw in ResourceLoader.get_dependencies(path):
		var dependency := _dependency_path(raw)
		if dependency != path and not result.has(dependency):
			result.append(dependency)
	result.sort()
	return result


func _recursive_dependencies(root_scene: String) -> Array[String]:
	var result: Array[String] = []
	var pending := _dependencies_for(root_scene)
	while not pending.is_empty():
		var current: String = pending.pop_front()
		if current == root_scene or result.has(current):
			continue
		result.append(current)
		for dependency in _dependencies_for(current):
			if dependency != root_scene and not result.has(dependency) and not pending.has(dependency):
				pending.append(dependency)
	result.sort()
	return result


func _file_record(path: String, kind: String, role := "") -> Dictionary:
	var hash := FileAccess.get_sha256(path)
	var size := FileAccess.get_size(path)
	if hash.is_empty() or size < 1:
		_fail("cannot hash provenance input: %s" % path)
		return {}
	var record := {"path": path, "kind": kind, "bytes": size, "sha256": hash}
	if not role.is_empty():
		record.role = role
		record.erase("kind")
	return record


func _resource_kind(path: String) -> String:
	match path.get_extension().to_lower():
		"tscn", "scn": return "scene"
		"tres", "res": return "resource"
		"gd", "cs": return "script"
		_: return "asset"


func _closure_digest(manifest: Dictionary) -> String:
	var lines: Array[String] = [
		DIGEST_HEADER,
		"source_kind\t%s" % manifest.source_kind,
		"root_scene\t%s" % manifest.root_scene,
		"engine_version\t%s" % manifest.engine_version,
		"export_preset_selector\t%s" % manifest.export_preset_selector
	]
	for entry in manifest.entries:
		lines.append("entry\t%s\t%s\t%d\t%s" % [entry.path, entry.kind, entry.bytes, entry.sha256])
	for tool in manifest.toolchain_inputs:
		lines.append("tool\t%s\t%s\t%d\t%s" % [tool.role, tool.path, tool.bytes, tool.sha256])
	var context := HashingContext.new()
	context.start(HashingContext.HASH_SHA256)
	context.update(("\n".join(lines) + "\n").to_utf8_buffer())
	return context.finish().hex_encode()


func _fail(message: String) -> void:
	_failed = true
	push_error(message)
	quit(2)
