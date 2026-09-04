extends Node3D

@export var target_path: NodePath


func _ready() -> void:
	var mesh := get_node_or_null(String(target_path) + "/Mesh") as MeshInstance3D
	var material := mesh.material_override as StandardMaterial3D if mesh != null else null
	var expected := Color(0.2, 0.7, 0.5, 1.0)
	if material == null or not material.albedo_color.is_equal_approx(expected):
		push_error("editable PackedScene internal material override did not survive load")
		get_tree().quit(2)
		return
	print("[PASS] editable PackedScene internal override loaded")
	get_tree().quit(0)


func _on_source_tree_exiting() -> void:
	pass
