extends SceneTree

## Copy/adapt this file into res://tests/ and run it through godot_capture.py --script.
## The fixture must instance the production player/controller/camera rig on a flat deterministic course.
## Run windowed when pause_action is supplied; headless displays may not enter captured mouse mode.
## This flat fixture cannot prove production-HUD event routing. Also run third_person_hud_mouse_probe.gd.
## Target-build hands-on review is still required for feel, sensitivity, focus loss, and capture recovery.

var _scene_path := ""
var _player_path := NodePath()
var _yaw_pivot_path := NodePath()
var _pitch_pivot_path := NodePath()
var _camera_path := NodePath()
var _spring_arm_path := NodePath()
var _obstacle_shape_path := NodePath()

var _move_forward := "move_forward"
var _look_right := "look_right"
var _look_up := "look_up"
var _zoom_out := "zoom_out"
var _recenter := "camera_recenter"
var _pause_action := ""
var _resume_action := ""

var _yaw_degrees: Array[float] = [45.0, 90.0]
var _move_frames := 20
var _look_frames := 8
var _zoom_frames := 8
var _recenter_frames := 20
var _settle_frames := 4
var _min_move_distance := 0.05
var _min_move_dot := 0.9
var _min_look_delta_degrees := 0.25
var _min_zoom_delta := 0.05
var _recenter_offset_degrees := 70.0
var _recenter_min_dot := 0.9
var _min_collision_delta := 0.05
var _collision_restore_tolerance := 0.1
var _mouse_delta := Vector2(30.0, 20.0)

var _active_actions: Array[StringName] = []


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

	var player := instance.get_node_or_null(_player_path) as Node3D
	var yaw_pivot := instance.get_node_or_null(_yaw_pivot_path) as Node3D
	var pitch_pivot := instance.get_node_or_null(_pitch_pivot_path) as Node3D
	var camera := instance.get_node_or_null(_camera_path) as Camera3D
	var spring_arm := instance.get_node_or_null(_spring_arm_path) as SpringArm3D if not _spring_arm_path.is_empty() else null
	var obstacle_shape := instance.get_node_or_null(_obstacle_shape_path) as CollisionShape3D if not _obstacle_shape_path.is_empty() else null

	if player == null or yaw_pivot == null or pitch_pivot == null or camera == null:
		_fail("player, yaw_pivot, pitch_pivot, and camera must resolve to Node3D/Camera3D nodes")
		return
	if not _spring_arm_path.is_empty() and spring_arm == null:
		_fail("spring_arm path does not resolve to SpringArm3D: %s" % _spring_arm_path)
		return
	if not _obstacle_shape_path.is_empty() and obstacle_shape == null:
		_fail("obstacle_shape path does not resolve to CollisionShape3D: %s" % _obstacle_shape_path)
		return

	for action in [_move_forward, _look_right, _look_up, _zoom_out, _recenter]:
		if action.is_empty() or not InputMap.has_action(action):
			_fail("Required input action is missing: %s" % action)
			return
	if not _pause_action.is_empty() and not InputMap.has_action(_pause_action):
		_fail("pause_action is missing: %s" % _pause_action)
		return
	if not _resume_action.is_empty() and not InputMap.has_action(_resume_action):
		_fail("resume_action is missing: %s" % _resume_action)
		return

	var initial_player_transform := player.global_transform
	var initial_yaw := yaw_pivot.rotation.y
	var initial_pitch := pitch_pivot.rotation.x

	for yaw_degrees in _yaw_degrees:
		_reset_player(player, initial_player_transform)
		yaw_pivot.rotation.y = initial_yaw + deg_to_rad(yaw_degrees)
		pitch_pivot.rotation.x = initial_pitch
		await _wait_physics(_settle_frames)
		var expected_forward := _flat_forward(camera)
		var before := player.global_position
		_press_action(_move_forward)
		await _wait_physics(_move_frames)
		_release_action(_move_forward)
		await _wait_physics(_settle_frames)
		var displacement := player.global_position - before
		displacement.y = 0.0
		if displacement.length() < _min_move_distance:
			_fail("Forward movement was too small after yaw %.1f: %.4f" % [yaw_degrees, displacement.length()])
			return
		var move_dot := displacement.normalized().dot(expected_forward)
		if move_dot < _min_move_dot:
			_fail("Forward movement is not camera-relative after yaw %.1f: dot=%.4f required=%.4f" % [yaw_degrees, move_dot, _min_move_dot])
			return
		print("[INFO] Camera-relative movement passed yaw=%.1f dot=%.4f distance=%.4f" % [yaw_degrees, move_dot, displacement.length()])

	_reset_player(player, initial_player_transform)
	yaw_pivot.rotation.y = initial_yaw
	pitch_pivot.rotation.x = initial_pitch
	await _wait_physics(_settle_frames)

	var yaw_before := yaw_pivot.rotation.y
	_press_action(_look_right)
	await _wait_process(_look_frames)
	_release_action(_look_right)
	if absf(rad_to_deg(angle_difference(yaw_before, yaw_pivot.rotation.y))) < _min_look_delta_degrees:
		_fail("Right-stick horizontal look action did not change yaw")
		return

	var pitch_before := pitch_pivot.rotation.x
	_press_action(_look_up)
	await _wait_process(_look_frames)
	_release_action(_look_up)
	if absf(rad_to_deg(angle_difference(pitch_before, pitch_pivot.rotation.x))) < _min_look_delta_degrees:
		_fail("Right-stick vertical look action did not change pitch")
		return

	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	yaw_before = yaw_pivot.rotation.y
	pitch_before = pitch_pivot.rotation.x
	var mouse_motion := InputEventMouseMotion.new()
	mouse_motion.relative = _mouse_delta
	Input.parse_input_event(mouse_motion)
	await _wait_process(_settle_frames)
	var mouse_yaw_delta := absf(rad_to_deg(angle_difference(yaw_before, yaw_pivot.rotation.y)))
	var mouse_pitch_delta := absf(rad_to_deg(angle_difference(pitch_before, pitch_pivot.rotation.x)))
	if mouse_yaw_delta < _min_look_delta_degrees or mouse_pitch_delta < _min_look_delta_degrees:
		_fail("Mouse motion did not change both orbit axes: yaw=%.4f pitch=%.4f" % [mouse_yaw_delta, mouse_pitch_delta])
		return
	print("[INFO] Flat-fixture mouse and right-stick X/Y orbit passed")
	print("[INFO] Run third_person_hud_mouse_probe.gd with the visible production HUD; this result alone does not prove GUI routing")

	if spring_arm != null:
		var zoom_before := spring_arm.spring_length
		_press_action(_zoom_out)
		await _wait_process(_zoom_frames)
		_release_action(_zoom_out)
		await _wait_physics(_settle_frames)
		var zoom_delta := absf(spring_arm.spring_length - zoom_before)
		if zoom_delta < _min_zoom_delta:
			_fail("Zoom action did not change SpringArm3D.spring_length: delta=%.4f" % zoom_delta)
			return
		print("[INFO] Zoom response passed delta=%.4f" % zoom_delta)

	var actor_forward := _flat_forward(player)
	yaw_pivot.rotation.y = initial_yaw + deg_to_rad(_recenter_offset_degrees)
	await _wait_process(_settle_frames)
	var recenter_before_dot := _flat_forward(camera).dot(actor_forward)
	_press_action(_recenter)
	await _wait_process(_recenter_frames)
	_release_action(_recenter)
	await _wait_process(_settle_frames)
	var recenter_after_dot := _flat_forward(camera).dot(actor_forward)
	if recenter_after_dot < _recenter_min_dot or recenter_after_dot <= recenter_before_dot + 0.05:
		_fail("Recenter did not align camera with current actor facing: before=%.4f after=%.4f required=%.4f" % [recenter_before_dot, recenter_after_dot, _recenter_min_dot])
		return
	print("[INFO] Recenter passed before_dot=%.4f after_dot=%.4f" % [recenter_before_dot, recenter_after_dot])

	if spring_arm != null and obstacle_shape != null:
		obstacle_shape.set_deferred("disabled", true)
		await _wait_physics(_settle_frames * 2)
		var clear_distance := spring_arm.global_position.distance_to(camera.global_position)
		obstacle_shape.set_deferred("disabled", false)
		await _wait_physics(_settle_frames * 3)
		var blocked_distance := spring_arm.global_position.distance_to(camera.global_position)
		if clear_distance - blocked_distance < _min_collision_delta:
			_fail("Camera collision did not shorten the rig: clear=%.4f blocked=%.4f" % [clear_distance, blocked_distance])
			return
		obstacle_shape.set_deferred("disabled", true)
		await _wait_physics(_settle_frames * 3)
		var restored_distance := spring_arm.global_position.distance_to(camera.global_position)
		if absf(restored_distance - clear_distance) > _collision_restore_tolerance:
			_fail("Camera distance did not restore after obstruction: clear=%.4f restored=%.4f tolerance=%.4f" % [clear_distance, restored_distance, _collision_restore_tolerance])
			return
		print("[INFO] SpringArm collision shorten/restore passed clear=%.4f blocked=%.4f restored=%.4f" % [clear_distance, blocked_distance, restored_distance])
	else:
		print("[SKIP] SpringArm collision fixture not supplied; target-build collision matrix remains required")
	print("[INFO] Camera collision does not prove player visibility; run third_person_visibility_probe.gd separately")

	if not _pause_action.is_empty():
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
		await _tap_action(_pause_action)
		await _wait_process(_settle_frames)
		if Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
			_fail("Pause did not release captured mouse mode")
			return
		var resume_action := _resume_action if not _resume_action.is_empty() else _pause_action
		await _tap_action(resume_action)
		await _wait_process(_settle_frames)
		if Input.mouse_mode != Input.MOUSE_MODE_CAPTURED:
			_fail("Resume did not restore captured mouse mode")
			return
		print("[INFO] Pause/resume mouse capture state passed")
	else:
		print("[SKIP] pause_action not supplied; target-build pause/focus capture recovery remains required")

	_release_all_actions()
	print("[PASS] Third-person controller probe passed")
	quit(0)


func _flat_forward(node: Node3D) -> Vector3:
	var forward := -node.global_transform.basis.z
	forward.y = 0.0
	return forward.normalized()


func _reset_player(player: Node3D, transform: Transform3D) -> void:
	player.global_transform = transform
	if player is CharacterBody3D:
		(player as CharacterBody3D).velocity = Vector3.ZERO


func _press_action(action: String) -> void:
	Input.action_press(action, 1.0)
	_active_actions.append(StringName(action))


func _release_action(action: String) -> void:
	Input.action_release(action)
	_active_actions.erase(StringName(action))


func _release_all_actions() -> void:
	for action in _active_actions:
		Input.action_release(action)
	_active_actions.clear()


func _tap_action(action: String) -> void:
	_press_action(action)
	await process_frame
	_release_action(action)
	await process_frame


func _wait_physics(frame_count: int) -> void:
	for _index in range(maxi(frame_count, 1)):
		await physics_frame


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
			"player": _player_path = NodePath(value)
			"yaw_pivot": _yaw_pivot_path = NodePath(value)
			"pitch_pivot": _pitch_pivot_path = NodePath(value)
			"camera": _camera_path = NodePath(value)
			"spring_arm": _spring_arm_path = NodePath(value)
			"obstacle_shape": _obstacle_shape_path = NodePath(value)
			"move_forward": _move_forward = value
			"look_right": _look_right = value
			"look_up": _look_up = value
			"zoom_out": _zoom_out = value
			"recenter": _recenter = value
			"pause_action": _pause_action = value
			"resume_action": _resume_action = value
			"yaw_degrees":
				_yaw_degrees.clear()
				for item in value.split(";", false):
					if not item.is_valid_float():
						return "yaw_degrees must be semicolon-separated numbers"
					_yaw_degrees.append(item.to_float())
			"move_frames": _move_frames = value.to_int()
			"look_frames": _look_frames = value.to_int()
			"zoom_frames": _zoom_frames = value.to_int()
			"recenter_frames": _recenter_frames = value.to_int()
			"settle_frames": _settle_frames = value.to_int()
			"min_move_distance": _min_move_distance = value.to_float()
			"min_move_dot": _min_move_dot = value.to_float()
			"min_look_delta_degrees": _min_look_delta_degrees = value.to_float()
			"min_zoom_delta": _min_zoom_delta = value.to_float()
			"recenter_offset_degrees": _recenter_offset_degrees = value.to_float()
			"recenter_min_dot": _recenter_min_dot = value.to_float()
			"min_collision_delta": _min_collision_delta = value.to_float()
			"collision_restore_tolerance": _collision_restore_tolerance = value.to_float()
			"mouse_delta":
				var parts := value.split(":", false)
				if parts.size() != 2 or not parts[0].is_valid_float() or not parts[1].is_valid_float():
					return "mouse_delta must be X:Y"
				_mouse_delta = Vector2(parts[0].to_float(), parts[1].to_float())
			_:
				return "Unknown user argument: %s" % key

	if not _scene_path.begins_with("res://"):
		return "scene must be a res:// path"
	if _player_path.is_empty() or _yaw_pivot_path.is_empty() or _pitch_pivot_path.is_empty() or _camera_path.is_empty():
		return "player, yaw_pivot, pitch_pivot, and camera are required"
	if _yaw_degrees.is_empty():
		return "yaw_degrees must not be empty"
	if _move_frames < 1 or _look_frames < 1 or _zoom_frames < 1 or _recenter_frames < 1 or _settle_frames < 1:
		return "frame counts must be positive"
	if _min_move_distance <= 0.0 or _min_move_dot < -1.0 or _min_move_dot > 1.0:
		return "movement thresholds are invalid"
	if _recenter_min_dot < -1.0 or _recenter_min_dot > 1.0:
		return "recenter_min_dot must be between -1 and 1"
	return ""


func _fail(message: String) -> void:
	_release_all_actions()
	printerr("[FAIL] %s" % message)
	quit(1)
