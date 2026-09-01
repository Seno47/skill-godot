extends SceneTree

var _failed := false

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
## schema-v5 typed lane-boundary terminations with road-end policy, query Y bounds and
## before/at/between/beyond XZ samples, vertex-resolved support contacts, source-role
## material masks and the raw-artifact manifest. The exporter itself injects the
## complete visible mesh/effective-material manifest, resolved marking-mesh chains and
## scene-authored building source-role manifest after traversing the scene. For physical
## closures it also overwrites sample base/topmost/covering mesh IDs from the exact
## visible render triangles. The adapter may classify meshes and declare sample points,
## but cannot invent marking endpoints/topmost hits or omit lamps, supports, markings,
## openings, trim, inconvenient mesh surfaces, or a visible road-end overlay.
## Before adapting the exporter, run its embedded PrimitiveMesh regression fixture:
## godot --headless --path . --script res://tests/streetscape_semantics_exporter.gd -- \
##   --self-test-primitive-mesh true
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
	if _option_is_true(options.get("self_test_primitive_mesh", false)):
		_run_primitive_mesh_regression()
		return
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
	if contract.get("schema_version") != 5:
		_fail("adapter result schema_version must be 5")
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
	if _failed:
		return
	if visible_mesh_manifest.is_empty():
		_fail("resolved production scene has no visible mesh instances")
		return
	contract["resolved_visible_mesh_manifest"] = visible_mesh_manifest
	var marking_mesh_chains := _collect_marking_mesh_chains(root)
	if _failed:
		return
	contract["resolved_marking_mesh_chains"] = marking_mesh_chains
	var building_source_roles := _collect_building_source_roles(root)
	if _failed:
		return
	contract["resolved_building_source_role_manifest"] = building_source_roles
	_resolve_road_end_topmost_samples(root, contract)
	if _failed:
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


func _resolve_road_end_topmost_samples(root: Node, contract: Dictionary) -> void:
	var raw_classifications: Variant = contract.get("visible_mesh_classifications", [])
	var raw_terminations: Variant = contract.get("lane_boundary_terminations", [])
	if not raw_classifications is Array or not raw_terminations is Array:
		_fail("road-end topmost evidence needs classification and termination arrays")
		return
	var classifications := {}
	for raw_classification in raw_classifications:
		if not raw_classification is Dictionary:
			_fail("visible mesh classification must be a Dictionary")
			return
		var classification: Dictionary = raw_classification
		var mesh_id := String(classification.get("mesh_instance_id", ""))
		if mesh_id.is_empty() or classifications.has(mesh_id):
			_fail("visible mesh classification ID is empty or duplicated")
			return
		classifications[mesh_id] = {
			"scope": String(classification.get("semantic_scope", "")),
			"class": String(classification.get("semantic_class", "")),
		}
	var triangles := _collect_visible_render_triangles(root)
	if _failed:
		return
	for raw_termination in raw_terminations:
		if not raw_termination is Dictionary:
			_fail("lane boundary termination must be a Dictionary")
			return
		var termination: Dictionary = raw_termination
		if String(termination.get("termination_kind", "")) != "physical_closure":
			continue
		var raw_relation: Variant = termination.get("road_substrate_relation")
		if not raw_relation is Dictionary:
			_fail("physical closure lacks road_substrate_relation")
			return
		var relation: Dictionary = raw_relation
		var ray_top_y := float(relation.get("ray_top_y", NAN))
		var ray_bottom_y := float(relation.get("ray_bottom_y", NAN))
		var raw_samples: Variant = relation.get("samples", [])
		if is_nan(ray_top_y) or is_nan(ray_bottom_y) or ray_top_y <= ray_bottom_y \
				or not raw_samples is Array or raw_samples.is_empty():
			_fail("physical closure has invalid topmost render-surface query")
			return
		for raw_sample in raw_samples:
			if not raw_sample is Dictionary:
				_fail("road/substrate sample must be a Dictionary")
				return
			var sample: Dictionary = raw_sample
			var raw_point: Variant = sample.get("point")
			if not raw_point is Array or raw_point.size() != 2:
				_fail("road/substrate sample point must contain X/Z")
				return
			var point := Vector2(float(raw_point[0]), float(raw_point[1]))
			var hits: Array[Dictionary] = []
			for triangle in triangles:
				var triangle_classification: Dictionary = classifications.get(
					String(triangle.mesh_id), {}
				)
				if String(triangle_classification.get("scope", "")) == "road_surface" \
						and String(triangle_classification.get("class", "")) == "road_marking":
					continue
				var height: Variant = _triangle_height_at_xz(
					point, triangle.a, triangle.b, triangle.c
				)
				if height == null or float(height) < ray_bottom_y or float(height) > ray_top_y:
					continue
				hits.append({"mesh_id": String(triangle.mesh_id), "height": float(height)})
			if hits.is_empty():
				_fail("road/substrate topmost query hit no visible render triangle")
				return
			hits.sort_custom(func(first: Dictionary, second: Dictionary) -> bool:
				return float(first.height) > float(second.height)
			)
			var topmost_mesh_id := String(hits[0].mesh_id)
			var topmost_height := float(hits[0].height)
			var coplanar_top_ids: Array[String] = []
			for hit in hits:
				if absf(float(hit.height) - topmost_height) > 0.001:
					break
				var coplanar_id := String(hit.mesh_id)
				if coplanar_id not in coplanar_top_ids:
					coplanar_top_ids.append(coplanar_id)
			coplanar_top_ids.sort()
			var base_mesh_id := topmost_mesh_id
			var base_index := 0
			for hit_index in hits.size():
				var hit_mesh_id := String(hits[hit_index].mesh_id)
				var hit_classification: Dictionary = classifications.get(hit_mesh_id, {})
				if String(hit_classification.get("scope", "")) == "road_surface" \
						and String(hit_classification.get("class", "")) == "road_surface":
					base_mesh_id = hit_mesh_id
					base_index = hit_index
					break
			var covering_ids: Array[String] = []
			for hit_index in base_index:
				var covering_id := String(hits[hit_index].mesh_id)
				if covering_id != base_mesh_id and covering_id not in covering_ids:
					covering_ids.append(covering_id)
			sample["source_kind"] = "exporter_resolved_topmost_render_mesh_sample"
			sample["mesh_instance_id"] = base_mesh_id
			sample["topmost_mesh_instance_id"] = topmost_mesh_id
			sample["covering_mesh_instance_ids"] = covering_ids
			sample["coplanar_top_mesh_instance_ids"] = coplanar_top_ids
		relation["source_kind"] = "exporter_resolved_topmost_render_mesh_samples"
		termination["road_substrate_relation"] = relation


func _collect_visible_render_triangles(root: Node) -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	var candidates: Array[Node] = []
	candidates.append_array(root.find_children("*", "MeshInstance3D", true, false))
	candidates.append_array(root.find_children("*", "MultiMeshInstance3D", true, false))
	for candidate in candidates:
		if not candidate is GeometryInstance3D or not candidate.is_visible_in_tree():
			continue
		var mesh_instance := candidate as MeshInstance3D
		var multi_mesh_instance := candidate as MultiMeshInstance3D
		var mesh: Mesh = null
		var transforms: Array[Transform3D] = []
		if mesh_instance != null:
			mesh = mesh_instance.mesh
			transforms.append(mesh_instance.global_transform)
		elif multi_mesh_instance != null and multi_mesh_instance.multimesh != null:
			mesh = multi_mesh_instance.multimesh.mesh
			var count := multi_mesh_instance.multimesh.visible_instance_count
			if count < 0:
				count = multi_mesh_instance.multimesh.instance_count
			for instance_index in count:
				transforms.append(
					multi_mesh_instance.global_transform
					* multi_mesh_instance.multimesh.get_instance_transform(instance_index)
				)
		if mesh == null:
			continue
		var mesh_id := String(root.get_path_to(candidate))
		if mesh is PrimitiveMesh:
			_append_triangle_arrays(
				result,
				mesh_id,
				transforms,
				(mesh as PrimitiveMesh).get_mesh_arrays()
			)
			if _failed:
				return []
			continue
		for surface_index in mesh.get_surface_count():
			if mesh.surface_get_primitive_type(surface_index) != Mesh.PRIMITIVE_TRIANGLES:
				continue
			_append_triangle_arrays(result, mesh_id, transforms, mesh.surface_get_arrays(surface_index))
			if _failed:
				return []
	return result


func _append_triangle_arrays(
		result: Array[Dictionary],
		mesh_id: String,
		transforms: Array[Transform3D],
		arrays: Array
) -> void:
	if arrays.size() <= Mesh.ARRAY_INDEX:
		_fail("render mesh arrays are incomplete: %s" % mesh_id)
		return
	var raw_vertices: Variant = arrays[Mesh.ARRAY_VERTEX]
	var raw_indices: Variant = arrays[Mesh.ARRAY_INDEX]
	if not raw_vertices is PackedVector3Array:
		_fail("render mesh has no PackedVector3Array vertices: %s" % mesh_id)
		return
	if raw_indices != null and not raw_indices is PackedInt32Array:
		_fail("render mesh has unsupported index data: %s" % mesh_id)
		return
	var vertices: PackedVector3Array = raw_vertices
	var indices := PackedInt32Array()
	if raw_indices is PackedInt32Array:
		indices = raw_indices
	if indices.is_empty() and vertices.size() % 3 != 0:
		_fail("non-indexed triangle mesh vertex count is not divisible by three: %s" % mesh_id)
		return
	if not indices.is_empty() and indices.size() % 3 != 0:
		_fail("triangle mesh index count is not divisible by three: %s" % mesh_id)
		return
	for index_value in indices:
		if index_value < 0 or index_value >= vertices.size():
			_fail("triangle mesh index is out of bounds: %s" % mesh_id)
			return
	for transform in transforms:
		if indices.is_empty():
			for vertex_index in range(0, vertices.size(), 3):
				result.append({
					"mesh_id": mesh_id,
					"a": transform * vertices[vertex_index],
					"b": transform * vertices[vertex_index + 1],
					"c": transform * vertices[vertex_index + 2],
				})
		else:
			for index_offset in range(0, indices.size(), 3):
				result.append({
					"mesh_id": mesh_id,
					"a": transform * vertices[indices[index_offset]],
					"b": transform * vertices[indices[index_offset + 1]],
					"c": transform * vertices[indices[index_offset + 2]],
				})


func _run_primitive_mesh_regression() -> void:
	var fixture := Node3D.new()
	fixture.name = "PrimitiveMeshRegressionFixture"
	get_root().add_child(fixture)
	var plane := MeshInstance3D.new()
	plane.name = "RoadPlaneMesh"
	plane.mesh = PlaneMesh.new()
	fixture.add_child(plane)
	var box := MeshInstance3D.new()
	box.name = "ClosureBoxMesh"
	box.mesh = BoxMesh.new()
	box.position = Vector3(3.0, 0.5, 0.0)
	fixture.add_child(box)

	var triangles := _collect_visible_render_triangles(fixture)
	if _failed:
		return
	var counts := {
		"RoadPlaneMesh": 0,
		"ClosureBoxMesh": 0,
	}
	for triangle in triangles:
		var mesh_id := String(triangle.get("mesh_id", ""))
		if counts.has(mesh_id):
			counts[mesh_id] = int(counts[mesh_id]) + 1
	if int(counts.RoadPlaneMesh) < 2:
		_fail("PrimitiveMesh regression did not collect PlaneMesh triangles")
		return
	if int(counts.ClosureBoxMesh) < 12:
		_fail("PrimitiveMesh regression did not collect BoxMesh triangles")
		return
	print("[PASS] streetscape-primitive-mesh-regression PlaneMesh=%d BoxMesh=%d" % [
		int(counts.RoadPlaneMesh), int(counts.ClosureBoxMesh)
	])
	fixture.free()
	quit(0)


func _triangle_height_at_xz(point: Vector2, a: Vector3, b: Vector3, c: Vector3) -> Variant:
	var denominator := (b.z - c.z) * (a.x - c.x) + (c.x - b.x) * (a.z - c.z)
	if absf(denominator) <= 0.000001:
		return null
	var weight_a := ((b.z - c.z) * (point.x - c.x) + (c.x - b.x) * (point.y - c.z)) / denominator
	var weight_b := ((c.z - a.z) * (point.x - c.x) + (a.x - c.x) * (point.y - c.z)) / denominator
	var weight_c := 1.0 - weight_a - weight_b
	if minf(weight_a, minf(weight_b, weight_c)) < -0.00001:
		return null
	return weight_a * a.y + weight_b * b.y + weight_c * c.y


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


func _option_is_true(value: Variant) -> bool:
	if value is bool:
		return value
	return str(value).to_lower() in ["1", "true", "yes", "on"]


func _fail(message: String) -> void:
	if _failed:
		return
	_failed = true
	push_error(message)
	quit(2)
