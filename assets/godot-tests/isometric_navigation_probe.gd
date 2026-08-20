extends SceneTree

## Copy into res://tests/ and point it at a deterministic project fixture.
## The adapter node must expose find_cell_path(Vector3i, Vector3i) -> Array/PackedVector3Array.
## If it exposes is_cell_walkable(Vector3i) -> bool, every returned cell is checked as well.

var _scene_path := ""
var _adapter_path := NodePath()
var _path_method := StringName("find_cell_path")
var _walkable_method := StringName("is_cell_walkable")
var _routes: Array[Dictionary] = []
var _allow_diagonal := true
var _require_height_change := false


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
	await process_frame

	var adapter := instance.get_node_or_null(_adapter_path)
	if adapter == null:
		_fail("Adapter node is missing: %s" % _adapter_path)
		return
	if not adapter.has_method(_path_method):
		_fail("Adapter is missing path method: %s" % _path_method)
		return
	var checks_walkability := adapter.has_method(_walkable_method)
	var saw_height_change := false

	for route in _routes:
		var start: Vector3i = route["start"]
		var goal: Vector3i = route["goal"]
		var raw_path = adapter.call(_path_method, start, goal)
		if not (raw_path is Array or raw_path is PackedVector3Array):
			_fail("Path method must return Array or PackedVector3Array route=%s>%s" % [start, goal])
			return
		if raw_path.is_empty():
			_fail("Path is empty route=%s>%s" % [start, goal])
			return

		var path: Array[Vector3i] = []
		for raw_cell in raw_path:
			var converted := _as_cell(raw_cell)
			if not converted["error"].is_empty():
				_fail(converted["error"])
				return
			path.append(converted["cell"])

		if path.front() != start or path.back() != goal:
			_fail(
				"Path endpoints disagree route=%s>%s actual=%s>%s"
				% [start, goal, path.front(), path.back()]
			)
			return

		for index in range(path.size()):
			var cell := path[index]
			if checks_walkability:
				var walkable_value = adapter.call(_walkable_method, cell)
				if not (walkable_value is bool) or not walkable_value:
					_fail("Path contains non-walkable cell=%s route=%s>%s" % [cell, start, goal])
					return
			if index == 0:
				continue
			var previous := path[index - 1]
			var delta := (cell - previous).abs()
			if delta == Vector3i.ZERO or delta.x > 1 or delta.y > 1 or delta.z > 1:
				_fail("Non-adjacent path step previous=%s current=%s" % [previous, cell])
				return
			if not _allow_diagonal and delta.x + delta.y + delta.z != 1:
				_fail("Diagonal/combined path step is forbidden previous=%s current=%s" % [previous, cell])
				return
			if delta.z > 0:
				saw_height_change = true

		print("[INFO] Isometric navigation route passed start=%s goal=%s cells=%d" % [start, goal, path.size()])

	if _require_height_change and not saw_height_change:
		_fail("No tested path exercised a height transition")
		return
	print("[PASS] Isometric navigation passed routes=%d" % _routes.size())
	quit(0)


func _parse_user_arguments() -> String:
	for argument in OS.get_cmdline_user_args():
		var separator := argument.find("=")
		if separator <= 0:
			return "Expected key=value user argument, got: %s" % argument
		var key := argument.substr(0, separator)
		var value := argument.substr(separator + 1)
		match key:
			"scene":
				_scene_path = value
			"adapter":
				_adapter_path = NodePath(value)
			"path_method":
				_path_method = StringName(value)
			"walkable_method":
				_walkable_method = StringName(value)
			"routes":
				_routes.clear()
				for route_text in value.split(";", false):
					var route_parts := route_text.split(">")
					if route_parts.size() != 2:
						return "Each route must be x:y:z>x:y:z, got: %s" % route_text
					var start_result := _parse_cell(route_parts[0])
					var goal_result := _parse_cell(route_parts[1])
					if not start_result["error"].is_empty():
						return start_result["error"]
					if not goal_result["error"].is_empty():
						return goal_result["error"]
					_routes.append({"start": start_result["cell"], "goal": goal_result["cell"]})
			"allow_diagonal":
				var diagonal_result := _parse_bool(value, "allow_diagonal")
				if not diagonal_result["error"].is_empty():
					return diagonal_result["error"]
				_allow_diagonal = diagonal_result["value"]
			"require_height_change":
				var height_result := _parse_bool(value, "require_height_change")
				if not height_result["error"].is_empty():
					return height_result["error"]
				_require_height_change = height_result["value"]
			_:
				return "Unknown user argument: %s" % key

	if not _scene_path.begins_with("res://"):
		return "scene must be a res:// path"
	if _adapter_path.is_empty():
		return "adapter is required"
	if _routes.is_empty():
		return "routes must not be empty"
	if _path_method.is_empty():
		return "path_method must not be empty"
	return ""


func _parse_cell(text: String) -> Dictionary:
	var parts := text.split(":")
	if parts.size() != 3:
		return {"error": "Each cell must be x:y:z, got: %s" % text}
	for part in parts:
		if not part.is_valid_int():
			return {"error": "Cell coordinates must be integers, got: %s" % text}
	return {
		"error": "",
		"cell": Vector3i(int(parts[0]), int(parts[1]), int(parts[2])),
	}


func _parse_bool(text: String, key: String) -> Dictionary:
	match text.to_lower():
		"true", "1", "yes":
			return {"error": "", "value": true}
		"false", "0", "no":
			return {"error": "", "value": false}
		_:
			return {"error": "%s must be true or false, got: %s" % [key, text]}


func _as_cell(value) -> Dictionary:
	if value is Vector3i:
		return {"error": "", "cell": value}
	if value is Vector3:
		var vector: Vector3 = value
		var rounded := Vector3i(roundi(vector.x), roundi(vector.y), roundi(vector.z))
		if vector.distance_to(Vector3(rounded)) <= 0.001:
			return {"error": "", "cell": rounded}
	return {"error": "Path contains a non-integral cell value: %s" % value}


func _fail(message: String) -> void:
	printerr("[FAIL] %s" % message)
	quit(1)
