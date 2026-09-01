extends SceneTree

var _failed := false

## Exact resolved-scene visible-first perimeter exporter shell.
## The production scene remains untouched. A project-owned QA adapter is loaded only
## by this headless process, added transiently after scene instantiation, and recorded
## as a provenance toolchain input rather than a production dependency.
##
## godot --headless --path . --script res://tests/visible_first_boundary_probe.gd -- \
##   --scene res://scenes/world/District.tscn \
##   --adapter-script res://scripts/qa/visible_first_boundary_adapter.gd \
##   --build-id district-target-v1 \
##   --output reports/visible-first-boundary-contract.json
##
## The adapter must implement:
##   export_visible_first_boundary(build_id: String, scene_path: String) -> Dictionary
## It must enumerate every enabled perimeter/safety collider from the instantiated
## production scene and issue PhysicsDirectSpaceState3D capsule sweeps or full-width
## ray bundles after at least one physics frame.
##
## Whole-body escape reachability is not adapter-owned. The production scene must have:
## - exactly one `production_boundary_reachability_region` node with scene metadata
##   `grid_origin_xz`, `grid_width`, `grid_height`, `cell_size`, `ray_top_y`,
##   `ray_bottom_y`, `ground_collision_mask`, `blocker_collision_mask`,
##   `query_margin`, and `safe_region_polygon_xz`;
## - one `production_boundary_reachability_hero_body` CollisionObject3D;
## - one enabled CapsuleShape3D CollisionShape3D in
##   `production_boundary_reachability_hero_shape`, below that body;
## - one or more Node3D starts in `production_boundary_reachability_start`.
## The exporter queries the resolved World3D itself and overwrites the adapter's
## `production_physics_reachability`; hard-coded free/blocked/outside cell lists cannot pass.


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var options := _parse_args(OS.get_cmdline_user_args())
	for required in ["scene", "adapter_script", "build_id", "output"]:
		if not options.has(required) or String(options[required]).is_empty():
			_fail("missing --%s" % required.replace("_", "-"))
			return

	var scene_path := String(options.scene)
	var adapter_path := String(options.adapter_script)
	if not scene_path.begins_with("res://") or not adapter_path.begins_with("res://"):
		_fail("--scene and --adapter-script must use res:// paths")
		return
	var packed := ResourceLoader.load(
		scene_path, "PackedScene", ResourceLoader.CACHE_MODE_REPLACE_DEEP
	) as PackedScene
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

	var adapter_script := ResourceLoader.load(
		adapter_path, "Script", ResourceLoader.CACHE_MODE_REPLACE_DEEP
	) as Script
	if adapter_script == null:
		_fail("could not load transient boundary adapter: %s" % adapter_path)
		return
	var adapter := Node3D.new()
	adapter.name = "TransientVisibleFirstBoundaryAdapter"
	adapter.set_script(adapter_script)
	root.add_child(adapter)
	await process_frame
	await physics_frame
	if not adapter.has_method("export_visible_first_boundary"):
		_fail("adapter must implement export_visible_first_boundary(build_id, scene_path)")
		return
	var raw: Variant = adapter.call(
		"export_visible_first_boundary", String(options.build_id), scene_path
	)
	if not raw is Dictionary:
		_fail("adapter export_visible_first_boundary must return Dictionary")
		return
	var contract: Dictionary = raw
	if contract.get("schema_version") != 2:
		_fail("adapter result schema_version must be 2")
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
	var production_reachability := _collect_production_physics_reachability(
		root, String(options.build_id), scene_path
	)
	if _failed:
		return
	contract["production_physics_reachability"] = production_reachability

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
	print("[PASS] visible-first-boundary-export build=%s scene=%s output=%s" % [
		String(options.build_id), scene_path, output_path
	])
	quit(0)


func _collect_production_physics_reachability(
	root: Node, build_id: String, scene_path: String
) -> Dictionary:
	var region_nodes := get_nodes_in_group("production_boundary_reachability_region")
	var hero_bodies := get_nodes_in_group("production_boundary_reachability_hero_body")
	var hero_shapes := get_nodes_in_group("production_boundary_reachability_hero_shape")
	var start_nodes := get_nodes_in_group("production_boundary_reachability_start")
	if region_nodes.size() != 1 or hero_bodies.size() != 1 or hero_shapes.size() != 1 \
			or start_nodes.is_empty():
		_fail("production boundary reachability groups are incomplete or ambiguous")
		return {}
	var region_node := region_nodes[0] as Node3D
	var hero_body := hero_bodies[0] as CollisionObject3D
	var hero_shape_node := hero_shapes[0] as CollisionShape3D
	if region_node == null or hero_body == null or hero_shape_node == null \
			or not root.is_ancestor_of(region_node) or not root.is_ancestor_of(hero_body) \
			or not root.is_ancestor_of(hero_shape_node) or hero_shape_node.disabled \
			or not hero_body.is_ancestor_of(hero_shape_node) \
			or not hero_shape_node.shape is CapsuleShape3D:
		_fail("production boundary reachability must use the resolved enabled hero capsule")
		return {}
	var required_metadata := [
		"grid_origin_xz", "grid_width", "grid_height", "cell_size", "ray_top_y",
		"ray_bottom_y", "ground_collision_mask", "blocker_collision_mask",
		"query_margin", "safe_region_polygon_xz",
	]
	for key in required_metadata:
		if not region_node.has_meta(key):
			_fail("production boundary reachability region lacks metadata: %s" % key)
			return {}
	var raw_origin: Variant = region_node.get_meta("grid_origin_xz")
	var raw_polygon: Variant = region_node.get_meta("safe_region_polygon_xz")
	if not raw_origin is Array or raw_origin.size() != 2 or not raw_polygon is Array \
			or raw_polygon.size() < 3:
		_fail("production boundary reachability region has invalid origin/polygon metadata")
		return {}
	var origin := Vector2(float(raw_origin[0]), float(raw_origin[1]))
	var width := int(region_node.get_meta("grid_width"))
	var height := int(region_node.get_meta("grid_height"))
	var cell_size := float(region_node.get_meta("cell_size"))
	var ray_top_y := float(region_node.get_meta("ray_top_y"))
	var ray_bottom_y := float(region_node.get_meta("ray_bottom_y"))
	var ground_mask := int(region_node.get_meta("ground_collision_mask"))
	var blocker_mask := int(region_node.get_meta("blocker_collision_mask"))
	var query_margin := float(region_node.get_meta("query_margin"))
	if width < 2 or height < 2 or cell_size <= 0.0 or ray_top_y <= ray_bottom_y \
			or ground_mask <= 0 or blocker_mask <= 0 or query_margin < 0.0:
		_fail("production boundary reachability region has invalid grid/query budgets")
		return {}
	var safe_polygon := PackedVector2Array()
	var serialized_polygon: Array[Array] = []
	for raw_point in raw_polygon:
		if not raw_point is Array or raw_point.size() != 2:
			_fail("production boundary reachability safe polygon point is invalid")
			return {}
		var point := Vector2(float(raw_point[0]), float(raw_point[1]))
		safe_polygon.append(point)
		serialized_polygon.append([point.x, point.y])
	var state: PhysicsDirectSpaceState3D = root.get_world_3d().direct_space_state
	var start_ground_query := PhysicsRayQueryParameters3D.create(
		Vector3(hero_body.global_position.x, ray_top_y, hero_body.global_position.z),
		Vector3(hero_body.global_position.x, ray_bottom_y, hero_body.global_position.z),
		ground_mask
	)
	start_ground_query.collide_with_areas = false
	start_ground_query.collide_with_bodies = true
	start_ground_query.exclude = [hero_body.get_rid()]
	var start_ground: Dictionary = state.intersect_ray(start_ground_query)
	if start_ground.is_empty():
		_fail("production hero start has no resolved render-supporting ground collision")
		return {}
	var start_ground_position: Vector3 = start_ground["position"]
	var body_ground_offset := hero_body.global_position.y - start_ground_position.y
	var relative_shape_transform := hero_body.global_transform.affine_inverse() \
		* hero_shape_node.global_transform
	var cell_rows: Array[Dictionary] = []
	var free_cells: Dictionary = {}
	for cell_z in height:
		for cell_x in width:
			var world_x := origin.x + (float(cell_x) + 0.5) * cell_size
			var world_z := origin.y + (float(cell_z) + 0.5) * cell_size
			var world_xz := Vector2(world_x, world_z)
			var inside_safe := Geometry2D.is_point_in_polygon(world_xz, safe_polygon)
			var ground_query := PhysicsRayQueryParameters3D.create(
				Vector3(world_x, ray_top_y, world_z),
				Vector3(world_x, ray_bottom_y, world_z),
				ground_mask
			)
			ground_query.collide_with_areas = false
			ground_query.collide_with_bodies = true
			ground_query.exclude = [hero_body.get_rid()]
			var ground_hit: Dictionary = state.intersect_ray(ground_query)
			var classification := "no_ground"
			var ground_y: Variant = null
			var ground_collider_id := ""
			if not ground_hit.is_empty():
				var ground_position: Vector3 = ground_hit["position"]
				ground_y = ground_position.y
				var body_transform := hero_body.global_transform
				body_transform.origin = Vector3(world_x, float(ground_y) + body_ground_offset, world_z)
				var shape_query := PhysicsShapeQueryParameters3D.new()
				shape_query.shape = hero_shape_node.shape
				shape_query.transform = body_transform * relative_shape_transform
				shape_query.collision_mask = blocker_mask
				shape_query.collide_with_areas = false
				shape_query.collide_with_bodies = true
				shape_query.margin = query_margin
				shape_query.exclude = [hero_body.get_rid()]
				classification = "blocked" if not state.intersect_shape(shape_query, 1).is_empty() else "free"
				var ground_collider: Variant = ground_hit.get("collider")
				if ground_collider is Node and root.is_ancestor_of(ground_collider):
					ground_collider_id = String(root.get_path_to(ground_collider))
			if classification == "free":
				free_cells[Vector2i(cell_x, cell_z)] = true
			cell_rows.append({
				"cell": [cell_x, cell_z],
				"world_xz": [world_x, world_z],
				"inside_safe_region": inside_safe,
				"classification": classification,
				"ground_y": ground_y,
				"ground_collider_id": ground_collider_id,
			})
	var start_rows: Array[Dictionary] = []
	for raw_start in start_nodes:
		var start := raw_start as Node3D
		if start == null or not root.is_ancestor_of(start):
			_fail("production boundary reachability start is outside the production scene")
			return {}
		var cell := Vector2i(
			floori((start.global_position.x - origin.x) / cell_size),
			floori((start.global_position.z - origin.y) / cell_size)
		)
		if cell.x < 0 or cell.y < 0 or cell.x >= width or cell.y >= height \
				or not free_cells.has(cell):
			_fail("production boundary reachability start does not resolve to a free grid cell")
			return {}
		start_rows.append({
			"node_path": String(root.get_path_to(start)),
			"world_position": [start.global_position.x, start.global_position.y, start.global_position.z],
			"cell": [cell.x, cell.y],
		})
	var capsule := hero_shape_node.shape as CapsuleShape3D
	return {
		"source_kind": "exporter_resolved_production_physics_grid",
		"build_id": build_id,
		"scene_path": scene_path,
		"physics_frame": Engine.get_physics_frames(),
		"region_node_path": String(root.get_path_to(region_node)),
		"hero_body_path": String(root.get_path_to(hero_body)),
		"hero_shape_path": String(root.get_path_to(hero_shape_node)),
		"hero_shape_class": "CapsuleShape3D",
		"hero_radius": capsule.radius,
		"hero_height": capsule.height,
		"grid_origin": [origin.x, origin.y],
		"grid_width": width,
		"grid_height": height,
		"cell_size": cell_size,
		"ground_collision_mask": ground_mask,
		"blocker_collision_mask": blocker_mask,
		"query_margin": query_margin,
		"safe_region_source_kind": "production_scene_metadata",
		"safe_region_polygon": serialized_polygon,
		"starts": start_rows,
		"cells": cell_rows,
	}


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
	if _failed:
		return
	_failed = true
	push_error(message)
	quit(2)
