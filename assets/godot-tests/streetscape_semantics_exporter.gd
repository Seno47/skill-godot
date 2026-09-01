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
## typed lane-boundary terminations, vertex-resolved support contacts, source-role
## material masks and the raw-artifact manifest. The exporter itself injects the
## complete visible mesh/effective-material manifest, resolved marking-mesh chains and
## scene-authored building source-role manifest after traversing the scene; the adapter
## may classify them but cannot invent marking endpoints or omit lamps, supports,
## markings, openings, trim, or inconvenient mesh surfaces.
##
## Every production marking MeshInstance3D belongs to `streetscape_marking_mesh` and
## carries authored metadata: `marking_chain_id`, `marking_class`, `marking_lane_ids`,
## `marking_surface_index`, and `marking_segment_vertex_pairs` (pairs of mesh vertex
## indices). The exporter resolves the actual final vertex positions into XZ segments.
## Every production building MeshInstance3D that contributes visible source roles belongs
## to `streetscape_building_source_roles`, carries `streetscape_building_object_id`, and
## carries `streetscape_source_roles`: an Array[Dictionary] with `role`, `source_kind`
## (`authored_mesh_surface` or `source_texture_uv_mask`) and `surface_indices`. UV roles
## additionally provide `source_texture_id`, `source_uv_mask_id`, and `uv_channel`.


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
	if contract.get("schema_version") != 4:
		_fail("adapter result schema_version must be 4")
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
	contract["resolved_marking_mesh_chains"] = _collect_marking_mesh_chains(root)
	contract["resolved_building_source_role_manifest"] = _collect_building_source_roles(root)

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


func _collect_marking_mesh_chains(root: Node) -> Array[Dictionary]:
	var chains: Dictionary = {}
	for raw_candidate in get_nodes_in_group("streetscape_marking_mesh"):
		if not raw_candidate is MeshInstance3D:
			_fail("streetscape_marking_mesh member must be MeshInstance3D")
			return []
		var candidate := raw_candidate as MeshInstance3D
		if not root.is_ancestor_of(candidate) or not candidate.is_visible_in_tree():
			continue
		if candidate.mesh == null:
			_fail("streetscape marking has no mesh: %s" % root.get_path_to(candidate))
			return []
		var chain_id := String(candidate.get_meta("marking_chain_id", ""))
		var marking_class := String(candidate.get_meta("marking_class", ""))
		var raw_lane_ids: Variant = candidate.get_meta("marking_lane_ids", [])
		var raw_pairs: Variant = candidate.get_meta("marking_segment_vertex_pairs", [])
		var surface_index := int(candidate.get_meta("marking_surface_index", -1))
		if chain_id.is_empty() or marking_class.is_empty() or not raw_lane_ids is Array \
				or not raw_pairs is Array or surface_index < 0 or surface_index >= candidate.mesh.get_surface_count():
			_fail("streetscape marking metadata is incomplete: %s" % root.get_path_to(candidate))
			return []
		var mesh_data := MeshDataTool.new()
		if mesh_data.create_from_surface(candidate.mesh, surface_index) != OK:
			_fail("could not read marking mesh surface: %s" % root.get_path_to(candidate))
			return []
		var lane_ids: Array[String] = []
		for raw_lane_id in raw_lane_ids:
			lane_ids.append(String(raw_lane_id))
		lane_ids.sort()
		var mesh_id := String(root.get_path_to(candidate))
		if not chains.has(chain_id):
			chains[chain_id] = {
				"id": chain_id,
				"source_kind": "resolved_marking_mesh_chain",
				"marking_class": marking_class,
				"lane_ids": lane_ids,
				"mesh_instance_ids": [],
				"segments": [],
			}
		var chain: Dictionary = chains[chain_id]
		if String(chain.marking_class) != marking_class or Array(chain.lane_ids) != lane_ids:
			_fail("marking chain metadata disagrees across meshes: %s" % chain_id)
			return []
		chain.mesh_instance_ids.append(mesh_id)
		for pair_index in raw_pairs.size():
			var raw_pair: Variant = raw_pairs[pair_index]
			if not raw_pair is Array or raw_pair.size() != 2:
				_fail("marking vertex pair must contain two indices: %s" % chain_id)
				return []
			var start_index := int(raw_pair[0])
			var end_index := int(raw_pair[1])
			if start_index < 0 or end_index < 0 or start_index >= mesh_data.get_vertex_count() \
					or end_index >= mesh_data.get_vertex_count():
				_fail("marking vertex pair is outside mesh: %s" % chain_id)
				return []
			var start_world := candidate.global_transform * mesh_data.get_vertex(start_index)
			var end_world := candidate.global_transform * mesh_data.get_vertex(end_index)
			chain.segments.append({
				"mesh_instance_id": mesh_id,
				"surface_index": surface_index,
				"measurement_source_kind": "resolved_mesh_vertices",
				"start_vertex_index": start_index,
				"end_vertex_index": end_index,
				"start": [start_world.x, start_world.z],
				"end": [end_world.x, end_world.z],
			})
		chains[chain_id] = chain
	var result: Array[Dictionary] = []
	for chain_id in chains.keys():
		var chain: Dictionary = chains[chain_id]
		chain.mesh_instance_ids.sort()
		if chain.mesh_instance_ids.is_empty() or chain.segments.is_empty():
			_fail("resolved marking chain is empty: %s" % chain_id)
			return []
		result.append(chain)
	result.sort_custom(func(first: Dictionary, second: Dictionary) -> bool:
		return String(first.id) < String(second.id)
	)
	return result


func _collect_building_source_roles(root: Node) -> Array[Dictionary]:
	var buildings: Dictionary = {}
	for raw_candidate in get_nodes_in_group("streetscape_building_source_roles"):
		if not raw_candidate is MeshInstance3D:
			_fail("streetscape_building_source_roles member must be MeshInstance3D")
			return []
		var candidate := raw_candidate as MeshInstance3D
		if not root.is_ancestor_of(candidate) or not candidate.is_visible_in_tree():
			continue
		if candidate.mesh == null:
			_fail("building source-role member has no mesh: %s" % root.get_path_to(candidate))
			return []
		var object_id := String(candidate.get_meta("streetscape_building_object_id", ""))
		var raw_roles: Variant = candidate.get_meta("streetscape_source_roles", [])
		if object_id.is_empty() or not raw_roles is Array or raw_roles.is_empty():
			_fail("building source-role metadata is incomplete: %s" % root.get_path_to(candidate))
			return []
		if not buildings.has(object_id):
			buildings[object_id] = {}
		var building_roles: Dictionary = buildings[object_id]
		var mesh_id := String(root.get_path_to(candidate))
		for raw_role in raw_roles:
			if not raw_role is Dictionary:
				_fail("building source role must be a Dictionary: %s" % mesh_id)
				return []
			var role_data: Dictionary = raw_role
			var role := String(role_data.get("role", ""))
			var source_kind := String(role_data.get("source_kind", ""))
			var raw_surface_indices: Variant = role_data.get("surface_indices", [])
			if role.is_empty() or source_kind not in ["authored_mesh_surface", "source_texture_uv_mask"] \
					or not raw_surface_indices is Array or raw_surface_indices.is_empty():
				_fail("building source role metadata is invalid: %s" % mesh_id)
				return []
			var role_entry: Dictionary
			if building_roles.has(role):
				role_entry = building_roles[role]
				if String(role_entry.get("source_kind", "")) != source_kind:
					_fail("building source role provenance disagrees across meshes: %s/%s" % [object_id, role])
					return []
			else:
				role_entry = {
					"role": role,
					"source_kind": source_kind,
					"mesh_surface_keys": [],
				}
				if source_kind == "source_texture_uv_mask":
					role_entry["source_texture_id"] = String(role_data.get("source_texture_id", ""))
					role_entry["source_uv_mask_id"] = String(role_data.get("source_uv_mask_id", ""))
					role_entry["uv_channel"] = int(role_data.get("uv_channel", -1))
					if String(role_entry.get("source_texture_id", "")).is_empty() \
							or String(role_entry.get("source_uv_mask_id", "")).is_empty() \
							or int(role_entry.get("uv_channel", -1)) < 0:
						_fail("building UV source role metadata is incomplete: %s/%s" % [object_id, role])
						return []
			if source_kind == "source_texture_uv_mask" and (
					String(role_entry.get("source_texture_id", "")) != String(role_data.get("source_texture_id", ""))
					or String(role_entry.get("source_uv_mask_id", "")) != String(role_data.get("source_uv_mask_id", ""))
					or int(role_entry.get("uv_channel", -1)) != int(role_data.get("uv_channel", -1))
			):
				_fail("building UV source role binding disagrees across meshes: %s/%s" % [object_id, role])
				return []
			var mesh_surface_keys: Array = role_entry.get("mesh_surface_keys", [])
			for raw_surface_index in raw_surface_indices:
				var surface_index := int(raw_surface_index)
				if surface_index < 0 or surface_index >= candidate.mesh.get_surface_count():
					_fail("building source role surface is outside mesh: %s/%s" % [object_id, role])
					return []
				var surface_key := "%s#%d" % [mesh_id, surface_index]
				if surface_key not in mesh_surface_keys:
					mesh_surface_keys.append(surface_key)
			mesh_surface_keys.sort()
			role_entry["mesh_surface_keys"] = mesh_surface_keys
			building_roles[role] = role_entry
		buildings[object_id] = building_roles
	var result: Array[Dictionary] = []
	for object_id in buildings.keys():
		var role_rows: Array[Dictionary] = []
		var building_roles: Dictionary = buildings[object_id]
		for role in building_roles.keys():
			role_rows.append(building_roles[role])
		role_rows.sort_custom(func(first: Dictionary, second: Dictionary) -> bool:
			return String(first.get("role", "")) < String(second.get("role", ""))
		)
		result.append({
			"object_id": String(object_id),
			"source_kind": "resolved_scene_building_source_roles",
			"roles": role_rows,
		})
	result.sort_custom(func(first: Dictionary, second: Dictionary) -> bool:
		return String(first.get("object_id", "")) < String(second.get("object_id", ""))
	)
	return result


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
