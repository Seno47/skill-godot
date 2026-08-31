extends SceneTree

## Exact resolved-scene exporter shell for the streetscape semantics contract.
## Copy into the game project, provide a scene-owned adapter node, then run:
## godot --headless --path . --script res://tests/streetscape_semantics_exporter.gd -- \
##   --scene res://scenes/world/District.tscn \
##   --adapter-script res://scripts/qa/streetscape_evidence_adapter.gd \
##   --build-id district-target-v1 \
##   --output reports/streetscape-semantics-contract.json
##
## The adapter script is loaded only by this QA process and must NOT be attached to,
## referenced by, or serialized inside the production scene. It must implement:
##   export_streetscape_semantics(build_id: String, scene_path: String) -> Dictionary
## It must read the instantiated production scene's final transforms, mesh surfaces,
## collision/hero-radius raster, semantic resources/groups, approach-side and
## T-opposite sidewalk/curb continuity bands, every visible road-detail footprint,
## lane-boundary terminations, support contacts, rendered surface-ID masks and the
## raw-artifact manifest. The exporter itself injects the complete visible mesh and
## effective-material manifest after traversing the resolved scene; the adapter may
## classify it but cannot omit lamps, supports or inconvenient mesh surfaces.


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var options := _parse_args(OS.get_cmdline_user_args())
	for required in ["scene", "adapter_script", "build_id", "output"]:
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

	var adapter_path := String(options.adapter_script)
	if not adapter_path.begins_with("res://"):
		_fail("--adapter-script must use a res:// path")
		return
	var adapter_script := ResourceLoader.load(
		adapter_path, "Script", ResourceLoader.CACHE_MODE_REPLACE_DEEP
	) as Script
	if adapter_script == null:
		_fail("could not load transient streetscape adapter: %s" % adapter_path)
		return
	var adapter := Node3D.new()
	adapter.name = "TransientStreetscapeEvidenceAdapter"
	adapter.set_script(adapter_script)
	root.add_child(adapter)
	await process_frame
	await physics_frame
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
	if contract.get("schema_version") != 3:
		_fail("adapter result schema_version must be 3")
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
	var visible_mesh_manifest := _collect_visible_mesh_manifest(root)
	if visible_mesh_manifest.is_empty():
		_fail("resolved production scene has no visible mesh instances")
		return
	contract["resolved_visible_mesh_manifest"] = visible_mesh_manifest

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


func _collect_visible_mesh_manifest(root: Node) -> Array[Dictionary]:
	var meshes: Array[Dictionary] = []
	var candidates: Array[Node] = []
	candidates.append_array(root.find_children("*", "MeshInstance3D", true, false))
	candidates.append_array(root.find_children("*", "MultiMeshInstance3D", true, false))
	for candidate in candidates:
		if not (candidate is GeometryInstance3D) or not candidate.is_visible_in_tree():
			continue
		var geometry := candidate as GeometryInstance3D
		var mesh_instance := candidate as MeshInstance3D
		var multi_mesh_instance := candidate as MultiMeshInstance3D
		var mesh: Mesh = null
		if mesh_instance != null:
			mesh = mesh_instance.mesh
		elif multi_mesh_instance != null and multi_mesh_instance.multimesh != null:
			mesh = multi_mesh_instance.multimesh.mesh
		if mesh == null or mesh.get_surface_count() <= 0:
			continue
		var node_path := String(root.get_path_to(candidate))
		var surfaces: Array[Dictionary] = []
		for surface_index in mesh.get_surface_count():
			var material: Material = null
			var source_kind := "missing"
			if geometry.material_override != null:
				material = geometry.material_override
				source_kind = "node_material_override"
			elif mesh_instance != null and mesh_instance.get_surface_override_material(surface_index) != null:
				material = mesh_instance.get_surface_override_material(surface_index)
				source_kind = "surface_override_material"
			else:
				material = mesh.surface_get_material(surface_index)
				if material != null:
					source_kind = "mesh_surface_material"
			surfaces.append({
				"surface_index": surface_index,
				"effective_material_id": _resource_id(
					material, "%s::surface-%d::missing" % [node_path, surface_index]
				),
				"material_source_kind": source_kind,
			})
		meshes.append({
			"id": node_path,
			"node_path": node_path,
			"mesh_resource_id": _resource_id(mesh, "%s::runtime-mesh" % node_path),
			"surface_count": mesh.get_surface_count(),
			"surfaces": surfaces,
		})
	meshes.sort_custom(func(first: Dictionary, second: Dictionary) -> bool:
		return String(first.id) < String(second.id)
	)
	return meshes


func _resource_id(resource: Resource, fallback: String) -> String:
	if resource == null:
		return fallback
	var path := String(resource.resource_path)
	return path if not path.is_empty() else fallback


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
