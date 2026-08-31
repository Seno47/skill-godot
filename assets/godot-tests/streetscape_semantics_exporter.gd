extends SceneTree

## Exact resolved-scene exporter shell for the streetscape semantics contract.
## Copy into the game project, provide a scene-owned adapter node, then run:
## godot --headless --path . --script res://tests/streetscape_semantics_exporter.gd -- \
##   --scene res://scenes/world/District.tscn \
##   --adapter-node StreetscapeEvidenceAdapter \
##   --build-id district-target-v1 \
##   --output reports/streetscape-semantics-contract.json
##
## The adapter must implement:
##   export_streetscape_semantics(build_id: String, scene_path: String) -> Dictionary
## It must read the instantiated production scene's final transforms, mesh surfaces,
## collision/hero-radius raster, semantic resources/groups, and raw-artifact manifest.


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var options := _parse_args(OS.get_cmdline_user_args())
	for required in ["scene", "adapter_node", "build_id", "output"]:
		if not options.has(required) or String(options[required]).is_empty():
			_fail("missing --%s" % required.replace("_", "-"))
			return

	var scene_path := String(options.scene)
	if not scene_path.begins_with("res://"):
		_fail("--scene must use a res:// path")
		return
	var packed := ResourceLoader.load(scene_path, "PackedScene", ResourceLoader.CACHE_MODE_REPLACE_DEEP) as PackedScene
	if packed == null:
		_fail("could not load production scene: %s" % scene_path)
		return
	var root := packed.instantiate(PackedScene.GEN_EDIT_STATE_DISABLED)
	if root == null:
		_fail("could not instantiate production scene: %s" % scene_path)
		return
	get_root().add_child(root)
	current_scene = root
	await process_frame
	await physics_frame

	var adapter := root.get_node_or_null(NodePath(String(options.adapter_node)))
	if adapter == null:
		_fail("streetscape adapter node is missing: %s" % String(options.adapter_node))
		return
	if not adapter.has_method("export_streetscape_semantics"):
		_fail("adapter must implement export_streetscape_semantics(build_id, scene_path)")
		return
	var raw: Variant = adapter.call(
		"export_streetscape_semantics", String(options.build_id), scene_path
	)
	if not raw is Dictionary:
		_fail("adapter export_streetscape_semantics must return Dictionary")
		return
	var contract: Dictionary = raw
	if contract.get("schema_version") != 1:
		_fail("adapter result schema_version must be 1")
		return
	if String(contract.get("build_id", "")) != String(options.build_id):
		_fail("adapter result build_id does not match --build-id")
		return
	var provenance: Variant = contract.get("scene_provenance")
	if not provenance is Dictionary:
		_fail("adapter result must include scene_provenance")
		return
	if String(provenance.get("source_kind", "")) != "resolved_target_scene":
		_fail("scene_provenance.source_kind must be resolved_target_scene")
		return
	if String(provenance.get("scene_path", "")) != scene_path:
		_fail("scene_provenance.scene_path must match the instantiated production scene")
		return

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
	output.store_string(JSON.stringify(contract, "  ") + "\n")
	output.close()
	print("[PASS] streetscape-semantics-export build=%s scene=%s output=%s" % [
		String(options.build_id), scene_path, output_path
	])
	quit(0)


func _parse_args(args: PackedStringArray) -> Dictionary:
	var result := {}
	var index := 0
	while index < args.size():
		var key := args[index]
		if key.begins_with("--") and index + 1 < args.size():
			result[key.trim_prefix("--").replace("-", "_")] = args[index + 1]
			index += 2
			continue
		index += 1
	return result


func _fail(message: String) -> void:
	push_error(message)
	quit(2)
