extends SceneTree

## Copy this file into res://tests/ and run it through godot_capture.py --script.
## The fixture should instance the real scene-authored button visuals without navigation side effects.

var _scene_path := ""
var _compound_button_path := NodePath()
var _compound_visual_path := NodePath()
var _icon_button_path := NodePath()
var _icon_visual_path := NodePath()
var _click_button_paths: Array[NodePath] = []
var _locales := PackedStringArray(["en"])
var _viewports: Array[Vector2i] = [Vector2i(336, 629)]
var _center_tolerance := 2.0


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

	var checked_states := 0
	for viewport_size in _viewports:
		root.size = viewport_size
		await process_frame
		for locale in _locales:
			TranslationServer.set_locale(locale)
			var instance := packed_scene.instantiate()
			root.add_child(instance)
			await process_frame
			await process_frame

			var compound_button := instance.get_node_or_null(_compound_button_path) as BaseButton
			var compound_visual := instance.get_node_or_null(_compound_visual_path) as Control
			var geometry_error := _center_error(
				compound_button,
				compound_visual,
				"compound",
				locale,
				viewport_size
			)
			if not geometry_error.is_empty():
				_fail(geometry_error)
				return

			if not _icon_button_path.is_empty():
				var icon_button := instance.get_node_or_null(_icon_button_path) as BaseButton
				var icon_visual := instance.get_node_or_null(_icon_visual_path) as Control
				geometry_error = _center_error(
					icon_button,
					icon_visual,
					"icon-only",
					locale,
					viewport_size
				)
				if not geometry_error.is_empty():
					_fail(geometry_error)
					return

			for click_path in _click_button_paths:
				var click_button := instance.get_node_or_null(click_path) as BaseButton
				var click_error := await _pointer_click_error(click_button, click_path)
				if not click_error.is_empty():
					_fail(
						"%s locale=%s viewport=%dx%d"
						% [click_error, locale, viewport_size.x, viewport_size.y]
					)
					return

			checked_states += 1
			print(
				"[INFO] Button composition passed locale=%s viewport=%dx%d"
				% [locale, viewport_size.x, viewport_size.y]
			)
			instance.queue_free()
			await process_frame

	print("[PASS] Button composition/click probe passed states=%d" % checked_states)
	quit(0)


func _center_error(
	button: BaseButton,
	visual: Control,
	kind: String,
	locale: String,
	viewport_size: Vector2i
) -> String:
	if button == null:
		return "%s button path is missing or not a BaseButton" % kind
	if visual == null:
		return "%s visual path is missing or not a Control" % kind
	if not button.is_visible_in_tree() or button.size.x <= 0.0 or button.size.y <= 0.0:
		return "%s button is not visible with a positive rect" % kind
	if not visual.is_visible_in_tree() or visual.size.x <= 0.0 or visual.size.y <= 0.0:
		return "%s visual is not visible with a positive rect" % kind

	var button_center := button.get_global_rect().get_center()
	var visual_center := visual.get_global_rect().get_center()
	var center_delta := button_center.distance_to(visual_center)
	if center_delta > _center_tolerance:
		return (
			"%s visual center drifted by %.3f px (tolerance %.3f) locale=%s viewport=%dx%d button_center=%s visual_center=%s"
			% [
				kind,
				center_delta,
				_center_tolerance,
				locale,
				viewport_size.x,
				viewport_size.y,
				button_center,
				visual_center,
			]
		)
	return ""


func _pointer_click_error(button: BaseButton, button_path: NodePath) -> String:
	if button == null:
		return "Click target is missing or not a BaseButton: %s" % button_path
	if button.disabled or not button.is_visible_in_tree():
		return "Click target is disabled or hidden: %s" % button_path

	var state := {"pressed": false}
	var on_pressed := func() -> void:
		state["pressed"] = true
	button.pressed.connect(on_pressed, CONNECT_ONE_SHOT)
	var center := button.get_global_rect().get_center()

	var motion := InputEventMouseMotion.new()
	motion.position = center
	motion.global_position = center
	motion.relative = Vector2.ZERO
	Input.parse_input_event(motion)
	await process_frame

	var press := InputEventMouseButton.new()
	press.button_index = MOUSE_BUTTON_LEFT
	press.position = center
	press.global_position = center
	press.pressed = true
	Input.parse_input_event(press)
	await process_frame

	var release := InputEventMouseButton.new()
	release.button_index = MOUSE_BUTTON_LEFT
	release.position = center
	release.global_position = center
	release.pressed = false
	Input.parse_input_event(release)
	await process_frame
	await process_frame

	if button.pressed.is_connected(on_pressed):
		button.pressed.disconnect(on_pressed)
	if not state["pressed"]:
		return "Pointer press/release did not emit pressed for %s" % button_path
	return ""


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
			"compound_button":
				_compound_button_path = NodePath(value)
			"compound_visual":
				_compound_visual_path = NodePath(value)
			"icon_button":
				_icon_button_path = NodePath(value)
			"icon_visual":
				_icon_visual_path = NodePath(value)
			"click_buttons":
				_click_button_paths.clear()
				for path in value.split(",", false):
					_click_button_paths.append(NodePath(path))
			"locales":
				_locales = value.split(",", false)
			"viewports":
				_viewports.clear()
				for viewport_value in value.split(",", false):
					var viewport_parts := viewport_value.to_lower().split("x")
					if (
						viewport_parts.size() != 2
						or not viewport_parts[0].is_valid_int()
						or not viewport_parts[1].is_valid_int()
					):
						return "Each viewport must be WIDTHxHEIGHT, got: %s" % viewport_value
					_viewports.append(Vector2i(int(viewport_parts[0]), int(viewport_parts[1])))
			"tolerance":
				if not value.is_valid_float():
					return "tolerance must be numeric, got: %s" % value
				_center_tolerance = value.to_float()
			_:
				return "Unknown user argument: %s" % key

	if not _scene_path.begins_with("res://"):
		return "scene must be a res:// path"
	if _compound_button_path.is_empty() or _compound_visual_path.is_empty():
		return "compound_button and compound_visual are required"
	if _icon_button_path.is_empty() != _icon_visual_path.is_empty():
		return "icon_button and icon_visual must be supplied together"
	if _click_button_paths.is_empty():
		_click_button_paths.append(_compound_button_path)
	if _locales.is_empty() or _viewports.is_empty():
		return "locales and viewports must not be empty"
	if _center_tolerance < 0.0:
		return "tolerance must be non-negative"
	for viewport_size in _viewports:
		if viewport_size.x < 1 or viewport_size.y < 1:
			return "viewport dimensions must be positive"
	return ""


func _fail(message: String) -> void:
	printerr("[FAIL] %s" % message)
	quit(1)
