extends SceneTree

## Copy/adapt this file into res://tests/ and run it through godot_capture.py --script.
## The fixture must instance the production camera/controller and real full-screen gameplay HUD.
## This probe injects InputEventMouseMotion through normal viewport routing; do not replace it with
## a direct controller method call. Target-build hands-on sensitivity review remains mandatory.

var _scene_path := ""
var _yaw_pivot_path := NodePath()
var _pitch_pivot_path := NodePath()
var _hud_root_path := NodePath()
var _mouse_delta := Vector2(30.0, 20.0)
var _settle_frames := 6
var _minimum_axis_delta_degrees := 0.25
var _minimum_hud_coverage := 0.9


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
		_fail("Could not load production-HUD fixture scene: %s" % _scene_path)
		return

	var instance := packed_scene.instantiate()
	root.add_child(instance)
	await process_frame
	await _wait_process(_settle_frames)

	var yaw_pivot := instance.get_node_or_null(_yaw_pivot_path) as Node3D
	var pitch_pivot := instance.get_node_or_null(_pitch_pivot_path) as Node3D
	var hud_root := instance.get_node_or_null(_hud_root_path) as Control
	if yaw_pivot == null or pitch_pivot == null or hud_root == null:
		_fail("yaw_pivot, pitch_pivot, and hud_root must resolve to Node3D/Control nodes")
		return
	if not hud_root.is_visible_in_tree():
		_fail("Production HUD root is not visible in the fixture")
		return

	var viewport_rect := instance.get_viewport().get_visible_rect()
	var hud_rect := hud_root.get_global_rect()
	var intersection := hud_rect.intersection(viewport_rect)
	var viewport_area := viewport_rect.get_area()
	var coverage := intersection.get_area() / viewport_area if viewport_area > 0.0 else 0.0
	if coverage < _minimum_hud_coverage:
		_fail(
			"HUD root covers only %.3f of the viewport; expected production full-screen HUD coverage >= %.3f"
			% [coverage, _minimum_hud_coverage]
		)
		return

	var yaw_before := yaw_pivot.rotation.y
	var pitch_before := pitch_pivot.rotation.x
	var event := InputEventMouseMotion.new()
	var center := viewport_rect.position + viewport_rect.size * 0.5
	event.position = center
	event.global_position = center
	event.relative = _mouse_delta
	Input.parse_input_event(event)
	await _wait_process(_settle_frames)

	var yaw_delta := absf(rad_to_deg(angle_difference(yaw_before, yaw_pivot.rotation.y)))
	var pitch_delta := absf(rad_to_deg(angle_difference(pitch_before, pitch_pivot.rotation.x)))
	if yaw_delta < _minimum_axis_delta_degrees or pitch_delta < _minimum_axis_delta_degrees:
		_fail(
			"HUD-routed InputEventMouseMotion did not change both orbit axes: yaw=%.4f pitch=%.4f required=%.4f; GUI may consume motion before _unhandled_input"
			% [yaw_delta, pitch_delta, _minimum_axis_delta_degrees]
		)
		return

	print(
		"[PASS] Production-HUD mouse routing passed coverage=%.3f yaw_delta=%.4f pitch_delta=%.4f; hands-on sensitivity remains required"
		% [coverage, yaw_delta, pitch_delta]
	)
	quit(0)


func _wait_process(frame_count: int) -> void:
	for _index in range(maxi(frame_count, 1)):
		await process_frame


func _parse_user_arguments() -> String:
	for argument in OS.get_cmdline_user_args():
		var separator := argument.find("=")
		if separator <= 0:
			return "Expected key=value user argument, got: %s" % argument
		var key := argument.substr(0, separator)
		var value := argument.substr(separator + 1)
		match key:
			"scene": _scene_path = value
			"yaw_pivot": _yaw_pivot_path = NodePath(value)
			"pitch_pivot": _pitch_pivot_path = NodePath(value)
			"hud_root": _hud_root_path = NodePath(value)
			"mouse_delta":
				var parts := value.split(":", false)
				if parts.size() != 2 or not parts[0].is_valid_float() or not parts[1].is_valid_float():
					return "mouse_delta must be X:Y"
				_mouse_delta = Vector2(parts[0].to_float(), parts[1].to_float())
			"settle_frames": _settle_frames = value.to_int()
			"minimum_axis_delta_degrees": _minimum_axis_delta_degrees = value.to_float()
			"minimum_hud_coverage": _minimum_hud_coverage = value.to_float()
			_:
				return "Unknown user argument: %s" % key

	if not _scene_path.begins_with("res://"):
		return "scene must be a res:// path"
	if _yaw_pivot_path.is_empty() or _pitch_pivot_path.is_empty() or _hud_root_path.is_empty():
		return "yaw_pivot, pitch_pivot, and hud_root are required"
	if is_zero_approx(_mouse_delta.x) or is_zero_approx(_mouse_delta.y):
		return "mouse_delta must exercise both axes"
	if _settle_frames < 1 or _minimum_axis_delta_degrees <= 0.0:
		return "settle_frames and minimum_axis_delta_degrees must be positive"
	if _minimum_hud_coverage <= 0.0 or _minimum_hud_coverage > 1.0:
		return "minimum_hud_coverage must be in (0, 1]"
	return ""


func _fail(message: String) -> void:
	printerr("[FAIL] %s" % message)
	quit(1)
