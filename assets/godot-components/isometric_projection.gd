@tool
class_name IsometricProjection
extends Resource

## Starting point for a fixed-angle 2D diamond grid.
## Copy into the project, save an external .tres instance, and keep all consumers on that instance.

@export var tile_size := Vector2(128.0, 64.0)
@export var elevation_step := 32.0
@export var origin := Vector2.ZERO


func is_valid_configuration() -> bool:
	return tile_size.x > 0.0 and tile_size.y > 0.0 and elevation_step >= 0.0


func grid_to_world(cell: Vector3i) -> Vector2:
	_assert_configuration()
	return origin + Vector2(
		(float(cell.x) - float(cell.y)) * tile_size.x * 0.5,
		(float(cell.x) + float(cell.y)) * tile_size.y * 0.5
			- float(cell.z) * elevation_step
	)


func world_to_grid(world_position: Vector2, elevation_level: int = 0) -> Vector3:
	_assert_configuration()
	var local := world_position - origin
	var projected_x := local.x / (tile_size.x * 0.5)
	var projected_y := (
		local.y + float(elevation_level) * elevation_step
	) / (tile_size.y * 0.5)
	return Vector3(
		(projected_x + projected_y) * 0.5,
		(projected_y - projected_x) * 0.5,
		float(elevation_level)
	)


func world_to_cell(world_position: Vector2, elevation_level: int = 0) -> Vector3i:
	var grid_position := world_to_grid(world_position, elevation_level)
	return Vector3i(
		roundi(grid_position.x),
		roundi(grid_position.y),
		elevation_level
	)


func cell_diamond(cell: Vector3i) -> PackedVector2Array:
	var center := grid_to_world(cell)
	var half_width := tile_size.x * 0.5
	var half_height := tile_size.y * 0.5
	return PackedVector2Array([
		center + Vector2(0.0, -half_height),
		center + Vector2(half_width, 0.0),
		center + Vector2(0.0, half_height),
		center + Vector2(-half_width, 0.0),
	])


func _assert_configuration() -> void:
	assert(
		is_valid_configuration(),
		"IsometricProjection requires positive tile_size and non-negative elevation_step."
	)
