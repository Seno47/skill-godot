extends SceneTree

## Copy into res://tests/ and run through godot_capture.py --script.
## The projection resource may use the bundled IsometricProjection component or a project adapter
## exposing grid_to_world(Vector3i), world_to_grid(Vector2, int), and world_to_cell(Vector2, int).

var _projection_path := ""
var _cells: Array[Vector3i] = [
	Vector3i.ZERO,
	Vector3i(1, 0, 0),
	Vector3i(0, 1, 0),
	Vector3i(-2, 3, 0),
	Vector3i(4, -1, 2),
]
var _epsilon := 0.001


func _initialize() -> void:
	var argument_error := _parse_user_arguments()
	if not argument_error.is_empty():
		printerr("[FAIL] %s" % argument_error)
		quit(2)
		return
	call_deferred("_run_probe")


func _run_probe() -> void:
	var projection = load(_projection_path)
	if projection == null:
		_fail("Could not load projection resource: %s" % _projection_path)
		return
	for method_name in [&"grid_to_world", &"world_to_grid", &"world_to_cell"]:
		if not projection.has_method(method_name):
			_fail("Projection is missing method: %s" % method_name)
			return

	for cell in _cells:
		var world_value = projection.call(&"grid_to_world", cell)
		if not (world_value is Vector2):
			_fail("grid_to_world must return Vector2 for cell=%s" % cell)
			return

		var grid_value = projection.call(&"world_to_grid", world_value, cell.z)
		if not (grid_value is Vector3):
			_fail("world_to_grid must return Vector3 for cell=%s" % cell)
			return
		var expected_grid := Vector3(cell)
		if grid_value.distance_to(expected_grid) > _epsilon:
			_fail(
				"Projection round-trip drift cell=%s world=%s grid=%s epsilon=%s"
				% [cell, world_value, grid_value, _epsilon]
			)
			return

		var recovered_value = projection.call(&"world_to_cell", world_value, cell.z)
		if not (recovered_value is Vector3i):
			_fail("world_to_cell must return Vector3i for cell=%s" % cell)
			return
		if recovered_value != cell:
			_fail(
				"Cell selection round-trip failed expected=%s recovered=%s world=%s"
				% [cell, recovered_value, world_value]
			)
			return

	print("[PASS] Isometric projection round-trip passed cells=%d" % _cells.size())
	quit(0)


func _parse_user_arguments() -> String:
	for argument in OS.get_cmdline_user_args():
		var separator := argument.find("=")
		if separator <= 0:
			return "Expected key=value user argument, got: %s" % argument
		var key := argument.substr(0, separator)
		var value := argument.substr(separator + 1)
		match key:
			"projection":
				_projection_path = value
			"cells":
				_cells.clear()
				for cell_text in value.split(";", false):
					var parsed := _parse_cell(cell_text)
					if not parsed["error"].is_empty():
						return parsed["error"]
					_cells.append(parsed["cell"])
			"epsilon":
				if not value.is_valid_float():
					return "epsilon must be numeric, got: %s" % value
				_epsilon = value.to_float()
			_:
				return "Unknown user argument: %s" % key

	if not _projection_path.begins_with("res://"):
		return "projection must be a res:// resource path"
	if _cells.is_empty():
		return "cells must not be empty"
	if _epsilon < 0.0:
		return "epsilon must be non-negative"
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


func _fail(message: String) -> void:
	printerr("[FAIL] %s" % message)
	quit(1)
