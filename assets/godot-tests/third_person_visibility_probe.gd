extends SceneTree

## Copy/adapt this file into res://tests/ and run it through godot_capture.py --script.
## The fixture must instance the production occlusion/cutaway system. Its adapter changes authored
## cases and reports production visual state; this probe owns the multi-height iterative ray checks.
## Rendered target-build review remains mandatory for silhouette quality and route readability.

var _scene_path := ""
var _adapter_path := NodePath()
var _desired_camera_path := NodePath()
var _sample_point_paths: Array[NodePath] = []
var _exclude_node_paths: Array[NodePath] = []
var _case_specs: Array[Dictionary] = []
var _collision_mask := 1
var _settle_frames := 6
var _max_hits_per_ray := 16
var _minimum_sample_count := 3


func _initialize() -> void:
	var argument_error := _parse_user_arguments()
	if not argument_error.is_empty():
		printerr("[FAIL] %s" % argument_error)
		quit(2)
		return
	call_deferred("_run_probe")


func _run_probe() -> void:
	var packed_scene := load(_scene_path) as PackedScene
	if packed_scene == null:
		_fail("Could not load fixture scene: %s" % _scene_path)
		return

	var instance := packed_scene.instantiate()
	root.add_child(instance)
	await process_frame
	await _wait_physics(_settle_frames)

	var adapter := instance.get_node_or_null(_adapter_path)
	var desired_camera := instance.get_node_or_null(_desired_camera_path) as Node3D
	if adapter == null or desired_camera == null:
		_fail("adapter and desired_camera must resolve")
		return

	var required_methods := [
		"probe_set_case",
		"probe_is_occluder_resolved",
		"probe_active_cutaway_count",
		"probe_is_silhouette_visible",
		"probe_restoration_issues",
		"probe_shell_issues",
	]
	for method_name in required_methods:
		if not adapter.has_method(method_name):
			_fail("Adapter is missing required method: %s" % method_name)
			return

	var sample_points: Array[Node3D] = []
	for path in _sample_point_paths:
		var sample := instance.get_node_or_null(path) as Node3D
		if sample == null:
			_fail("sample_points path does not resolve to Node3D: %s" % path)
			return
		sample_points.append(sample)
	if sample_points.size() < _minimum_sample_count:
		_fail("At least %d authored player visibility samples are required; got %d" % [_minimum_sample_count, sample_points.size()])
		return

	var excluded_rids: Array[RID] = []
	for path in _exclude_node_paths:
		var excluded_node := instance.get_node_or_null(path)
		if excluded_node == null:
			_fail("exclude_nodes path does not resolve: %s" % path)
			return
		_collect_collision_rids(excluded_node, excluded_rids)

	var space_state: PhysicsDirectSpaceState3D = instance.get_world_3d().direct_space_state
	for spec in _case_specs:
		var case_name := String(spec["name"])
		var minimum_occluders := int(spec["minimum_occluders"])
		var expected_mode := String(spec["mode"])
		adapter.call("probe_set_case", case_name)
		await process_frame
		await _wait_physics(_settle_frames)

		var unique_occluders: Dictionary = {}
		var maximum_occluders_on_one_ray := 0
		for sample in sample_points:
			var hits := _collect_occluders(
				space_state,
				desired_camera.global_position,
				sample.global_position,
				excluded_rids
			)
			maximum_occluders_on_one_ray = maxi(maximum_occluders_on_one_ray, hits.size())
			for collider in hits:
				unique_occluders[collider.get_instance_id()] = collider

		var unique_count := unique_occluders.size()
		if expected_mode == "clear":
			if unique_count != 0:
				_fail("Clear/open-hole case %s has %d camera-player occluder(s); camera-only proxy may cover a visible opening" % [case_name, unique_count])
				return
			if int(adapter.call("probe_active_cutaway_count")) != 0:
				_fail("Clear case %s retained active cutaway state" % case_name)
				return
			if bool(adapter.call("probe_is_silhouette_visible")):
				_fail("Clear case %s retained the silhouette fallback" % case_name)
				return
			var restoration_error := _string_list_error(adapter.call("probe_restoration_issues"), "restoration", case_name)
			if not restoration_error.is_empty():
				_fail(restoration_error)
				return
		else:
			if unique_count < minimum_occluders:
				_fail("Blocked case %s found %d unique occluder(s); expected at least %d" % [case_name, unique_count, minimum_occluders])
				return
			if minimum_occluders > 1 and maximum_occluders_on_one_ray < minimum_occluders:
				_fail("Multi-occluder case %s did not place at least %d simultaneous blockers on one player sample ray" % [case_name, minimum_occluders])
				return

			if expected_mode == "cutaway":
				for collider in unique_occluders.values():
					if not bool(adapter.call("probe_is_occluder_resolved", collider)):
						_fail("Cutaway case %s left an unresolved occluder: %s" % [case_name, collider.name])
						return
				if bool(adapter.call("probe_is_silhouette_visible")):
					_fail("Cutaway case %s enabled silhouette fallback unexpectedly" % case_name)
					return
				if int(adapter.call("probe_active_cutaway_count")) < 1:
					_fail("Cutaway case %s reports no active cutaway state" % case_name)
					return
			elif expected_mode == "silhouette":
				if not bool(adapter.call("probe_is_silhouette_visible")):
					_fail("Silhouette fallback case %s did not enable the silhouette" % case_name)
					return

		var shell_error := _string_list_error(adapter.call("probe_shell_issues", case_name), "render/collision shell", case_name)
		if not shell_error.is_empty():
			_fail(shell_error)
			return

		print(
			"[INFO] Visibility case passed name=%s mode=%s unique_occluders=%d max_on_one_ray=%d samples=%d"
			% [case_name, expected_mode, unique_count, maximum_occluders_on_one_ray, sample_points.size()]
		)

	print("[PASS] Third-person player visibility probe passed cases=%d" % _case_specs.size())
	quit(0)


func _collect_occluders(
	space_state: PhysicsDirectSpaceState3D,
	from: Vector3,
	to: Vector3,
	base_excludes: Array[RID]
) -> Array[CollisionObject3D]:
	var hits: Array[CollisionObject3D] = []
	var excludes := base_excludes.duplicate()
	for _index in range(_max_hits_per_ray):
		var query := PhysicsRayQueryParameters3D.create(from, to)
		query.collision_mask = _collision_mask
		query.exclude = excludes
		query.collide_with_areas = true
		query.collide_with_bodies = true
		query.hit_from_inside = true
		var result := space_state.intersect_ray(query)
		if result.is_empty():
			break
		var collider := result.get("collider") as CollisionObject3D
		if collider == null:
			break
		var collider_rid := collider.get_rid()
		if collider_rid in excludes:
			break
		hits.append(collider)
		excludes.append(collider_rid)
	return hits


func _collect_collision_rids(node: Node, output: Array[RID]) -> void:
	if node is CollisionObject3D:
		var rid := (node as CollisionObject3D).get_rid()
		if rid.is_valid() and rid not in output:
			output.append(rid)
	for child in node.get_children():
		_collect_collision_rids(child, output)


func _string_list_error(value: Variant, label: String, case_name: String) -> String:
	if not (value is Array or value is PackedStringArray):
		return "Adapter %s issues for case %s must be an Array or PackedStringArray" % [label, case_name]
	var issues: Array[String] = []
	for item in value:
		var text := String(item).strip_edges()
		if not text.is_empty():
			issues.append(text)
	if issues.is_empty():
		return ""
	return "%s issues for case %s: %s" % [label.capitalize(), case_name, "; ".join(issues)]


func _wait_physics(frame_count: int) -> void:
	for _index in range(maxi(frame_count, 1)):
		await physics_frame


func _parse_user_arguments() -> String:
	for argument in OS.get_cmdline_user_args():
		var separator := argument.find("=")
		if separator <= 0:
			return "Expected key=value user argument, got: %s" % argument
		var key := argument.substr(0, separator)
		var value := argument.substr(separator + 1)
		match key:
			"scene": _scene_path = value
			"adapter": _adapter_path = NodePath(value)
			"desired_camera": _desired_camera_path = NodePath(value)
			"sample_points":
				_sample_point_paths.clear()
				for path in value.split(";", false):
					_sample_point_paths.append(NodePath(path))
			"exclude_nodes":
				_exclude_node_paths.clear()
				for path in value.split(";", false):
					_exclude_node_paths.append(NodePath(path))
			"cases":
				_case_specs.clear()
				for item in value.split(";", false):
					var parts := item.split(":", false)
					if parts.size() != 3 or not parts[1].is_valid_int():
						return "Each case must be NAME:MIN_OCCLUDERS:clear|cutaway|silhouette"
					var mode := String(parts[2])
					if mode not in ["clear", "cutaway", "silhouette"]:
						return "Unknown visibility case mode: %s" % mode
					var minimum_occluders := int(parts[1])
					if minimum_occluders < 0 or (mode == "clear" and minimum_occluders != 0):
						return "Clear cases require 0 occluders; blocked cases require a non-negative minimum"
					_case_specs.append({
						"name": String(parts[0]),
						"minimum_occluders": minimum_occluders,
						"mode": mode,
					})
			"collision_mask":
				if not value.is_valid_int():
					return "collision_mask must be an integer"
				_collision_mask = value.to_int()
			"settle_frames": _settle_frames = value.to_int()
			"max_hits_per_ray": _max_hits_per_ray = value.to_int()
			"minimum_sample_count": _minimum_sample_count = value.to_int()
			_:
				return "Unknown user argument: %s" % key

	if not _scene_path.begins_with("res://"):
		return "scene must be a res:// path"
	if _adapter_path.is_empty() or _desired_camera_path.is_empty():
		return "adapter and desired_camera are required"
	if _sample_point_paths.is_empty() or _case_specs.is_empty():
		return "sample_points and cases must not be empty"
	if _collision_mask < 1 or _settle_frames < 1 or _max_hits_per_ray < 1 or _minimum_sample_count < 2:
		return "collision_mask and probe counts must be positive; minimum_sample_count must be at least 2"
	return ""


func _fail(message: String) -> void:
	printerr("[FAIL] %s" % message)
	quit(1)
