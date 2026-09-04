extends Control
## Mechanism fixture, not finished game art. All visible nodes are scene-authored.

@export var broken: bool = false
@export var reduced_motion: bool = false
var clicks: int = 0
var completed_work: int = 0
var elapsed: float = 0.0
var press_tween: Tween
var reward_tween: Tween
var panel_tween: Tween
var panel_open: bool = false
var last_cycle: int = -1
@onready var action: Button = $Click/Action
@onready var face: Control = $Click/Action/Face
@onready var token: Polygon2D = $Click/Token
@onready var follower: PathFollow2D = $Travel/Route/Follower
@onready var panel: Control = $Panel/Drawer

func _ready() -> void:
	broken = broken or "--broken" in OS.get_cmdline_user_args()
	reduced_motion = reduced_motion or "--reduced-motion" in OS.get_cmdline_user_args()
	face.pivot_offset = face.size * 0.5
	if broken:
		$Work/Part.position.x = 245.0
	$Header.text = "MOTION LAB  /  " + ("DELIBERATELY BROKEN" if broken else "REFERENCE MECHANISMS")
	if "--self-test" in OS.get_cmdline_user_args():
		_run_probe.call_deferred()
	elif "--capture" in OS.get_cmdline_user_args():
		_capture_sequence.call_deferred()

func _process(delta: float) -> void:
	elapsed += delta
	var phase := fmod(elapsed, 5.0) / 5.0
	# Same speed envelope, with deliberate tangent failure in the negative case.
	follower.progress_ratio = smoothstep(0.0, 1.0, phase)
	follower.rotates = not broken
	if broken:
		follower.rotation = 0.0
	var cycle := int(elapsed / 2.2)
	if cycle != last_cycle:
		last_cycle = cycle
		$Work/AnimationPlayer.play("stamp")

func _on_action_pressed() -> void:
	clicks += 1 # Simulation outcome is never owned by a cosmetic tween callback.
	$Click/Count.text = "Collected: %d" % clicks
	if press_tween:
		press_tween.kill()
	face.scale = Vector2(0.94, 0.94) if not reduced_motion else Vector2.ONE
	press_tween = create_tween()
	press_tween.tween_property(face, "scale", Vector2.ONE, 0.14).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	if reward_tween:
		reward_tween.kill()
	token.position = Vector2(150, 120)
	token.modulate.a = 1.0
	reward_tween = create_tween()
	if reduced_motion:
		token.position = Vector2(322, 58)
		reward_tween.tween_property(token, "modulate:a", 0.0, 0.12)
	else:
		reward_tween.tween_method(_reward_position, 0.0, 1.0, 0.45)
		reward_tween.tween_property(token, "modulate:a", 0.0, 0.1)
	if broken:
		face.scale = Vector2(1.3, 0.75)
		face.pivot_offset = Vector2.ZERO

func _reward_position(t: float) -> void:
	var from := Vector2(150, 120)
	var to := Vector2(322, 58)
	var control := Vector2(238, 4)
	token.position = from.lerp(control, t).lerp(control.lerp(to, t), t)

func _on_work_contact() -> void:
	completed_work += 1
	$Work/Count.text = "Stamped: %d" % completed_work
	$Work/Part.color = Color("e8bf72") if completed_work % 2 else Color("78bba6")
	if broken:
		$Work/Head.position.x = 85.0 # Contact visibly misses the part.

func _on_toggle_pressed() -> void:
	panel_open = not panel_open
	if panel_tween:
		panel_tween.kill()
	panel.mouse_filter = Control.MOUSE_FILTER_STOP if panel_open else Control.MOUSE_FILTER_IGNORE
	var target := Vector2(180, 62) if panel_open else Vector2(180, 78)
	if reduced_motion:
		panel.position = target
		panel.modulate.a = float(panel_open)
		return
	panel_tween = create_tween().set_parallel(true)
	panel_tween.tween_property(panel, "position", target, 0.18).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	panel_tween.tween_property(panel, "modulate:a", float(panel_open), 0.14)

func _pointer_click(button: Button) -> void:
	var location := button.get_global_rect().get_center()
	var motion := InputEventMouseMotion.new()
	motion.position = location
	get_viewport().push_input(motion, true)
	for down in [true, false]:
		var event := InputEventMouseButton.new()
		event.position = location
		event.global_position = location
		event.button_index = MOUSE_BUTTON_LEFT
		event.pressed = down
		get_viewport().push_input(event, true)
		await get_tree().process_frame

func _capture_sequence() -> void:
	await get_tree().process_frame
	for index in range(8):
		await _pointer_click(action)
		if index % 2 == 0:
			await _pointer_click($Panel/Toggle)
		await get_tree().create_timer(0.7).timeout

func _run_probe() -> void:
	await get_tree().process_frame
	await get_tree().process_frame
	var errors: Array[String] = []
	var shell := action.get_global_rect()
	for index in range(12):
		await _pointer_click(action)
	await get_tree().create_timer(0.6).timeout
	if clicks != 12:
		errors.append("pointer dispatch/settlement mismatch: %d" % clicks)
	if not face.scale.is_equal_approx(Vector2.ONE) or action.get_global_rect() != shell:
		errors.append("press settle/layout drift")
	if not face.pivot_offset.is_equal_approx(face.size * 0.5):
		errors.append("press pivot moved off-center")
	for index in range(5):
		await _pointer_click($Panel/Toggle)
	await get_tree().create_timer(0.3).timeout
	if not panel_open or panel.modulate.a < 0.99 or not panel.position.is_equal_approx(Vector2(180, 62)):
		errors.append("interrupted panel did not settle")
	var curve: Curve2D = $Travel/Route.curve
	for fraction in [0.1, 0.32, 0.55, 0.8]:
		follower.progress_ratio = fraction
		var distance := follower.progress
		var tangent := (curve.sample_baked(distance + 0.5) - curve.sample_baked(distance - 0.5)).angle()
		if absf(angle_difference(follower.rotation, tangent)) > 0.12:
			errors.append("travel facing disagrees with tangent")
	# Probe the real authored contact frame, not a hand-entered target position.
	$Work/AnimationPlayer.seek(0.46, true)
	if absf($Work/Head.position.x - $Work/Part.position.x) > 0.5 or absf($Work/Head.position.y + 10.0 - $Work/Part.position.y) > 0.5:
		errors.append("work contact misses the part")
	if completed_work < 1:
		errors.append("authored contact event never ran")
	print("[MECHANISM_PASS]" if errors.is_empty() else "[MECHANISM_FAIL] " + str(errors))
	print("This probe does not certify aesthetic quality or normal-speed watchback.")
	get_tree().quit(0 if errors.is_empty() else 1)
