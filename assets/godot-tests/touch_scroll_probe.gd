extends SceneTree

## Copy this file into res://tests/ and run it through godot_capture.py --script.
## The fixture scene must open the UI in a visible, overflowing state.

var _scene_path := ""
var _target_path := NodePath()
var _viewport_size := Vector2i(336, 629)
var _drag_distance := 160.0
var _drag_steps := 4


func _initialize() -> void:
	var argument_error := _parse_user_arguments()
	if not argument_error.is_empty():
		printerr("[FAIL] %s" % argument_error)
		quit(2)
		return
	call_deferred("_run_probe")


func _run_probe() -> void:
	root.size = _viewport_size
	var packed_scene := load(_scene_path) as PackedScene
	if packed_scene == null:
		_fail("Could not load fixture scene: %s" % _scene_path)
		return

	var instance := packed_scene.instantiate()
	root.add_child(instance)
	await process_frame
	await process_frame

	var target := instance.get_node_or_null(_target_path) as ScrollContainer
	if target == null:
		_fail("Target is not a ScrollContainer: %s" % _target_path)
		return
	if not target.is_visible_in_tree() or target.size.x <= 0.0 or target.size.y <= 0.0:
		_fail("Target is not visible with a positive runtime rect: %s" % _target_path)
		return

	var scroll_bar := target.get_v_scroll_bar()
	if scroll_bar.max_value <= scroll_bar.page:
		_fail(
			"Target has no vertical overflow: max=%s page=%s"
			% [scroll_bar.max_value, scroll_bar.page]
		)
		return

	target.scroll_vertical = 0
	await process_frame
	var before := target.scroll_vertical
	var start := target.get_global_rect().get_center()

	var press := InputEventScreenTouch.new()
	press.index = 0
	press.position = start
	press.pressed = true
	target._gui_input(press)
	await process_frame

	var step_delta := Vector2(0.0, -_drag_distance / float(_drag_steps))
	var current := start
	for _step in range(_drag_steps):
		current += step_delta
		var drag := InputEventScreenDrag.new()
		drag.index = 0
		drag.position = current
		drag.relative = step_delta
		drag.velocity = step_delta * 60.0
		target._gui_input(drag)
		await process_frame

	var release := InputEventScreenTouch.new()
	release.index = 0
	release.position = current
	release.pressed = false
	target._gui_input(release)
	for _frame in range(3):
		await process_frame

	var after := target.scroll_vertical
	if after <= before:
		_fail("Touch drag did not increase scroll_vertical: before=%d after=%d" % [before, after])
		return

	print(
		"[PASS] Touch scroll moved target=%s viewport=%dx%d before=%d after=%d"
		% [_target_path, _viewport_size.x, _viewport_size.y, before, after]
	)
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
			"target":
				_target_path = NodePath(value)
			"viewport":
				var parts := value.to_lower().split("x")
				if parts.size() != 2 or not parts[0].is_valid_int() or not parts[1].is_valid_int():
					return "viewport must be WIDTHxHEIGHT, got: %s" % value
				_viewport_size = Vector2i(int(parts[0]), int(parts[1]))
			"drag_distance":
				if not value.is_valid_float():
					return "drag_distance must be numeric, got: %s" % value
				_drag_distance = value.to_float()
			"drag_steps":
				if not value.is_valid_int():
					return "drag_steps must be an integer, got: %s" % value
				_drag_steps = value.to_int()
			_:
				return "Unknown user argument: %s" % key

	if not _scene_path.begins_with("res://"):
		return "scene must be a res:// path"
	if _target_path.is_empty():
		return "target must be a node path relative to the fixture root"
	if _viewport_size.x < 1 or _viewport_size.y < 1:
		return "viewport dimensions must be positive"
	if _drag_distance <= 0.0 or _drag_steps < 1:
		return "drag_distance and drag_steps must be positive"
	return ""


func _fail(message: String) -> void:
	printerr("[FAIL] %s" % message)
	quit(1)
