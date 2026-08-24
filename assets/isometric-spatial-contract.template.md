# Isometric / 2.5D Spatial Contract

Project: `[name]`  
Decision owner/date: `[owner] / [date]`

## Architecture

- Primary model: `[2D diamond | orthographic 3D | hybrid]`
- Authoritative simulation space: `[grid | 2D world | 3D world]`
- Renderer and target platforms: `[values]`
- Reason this model fits the game: `[short decision]`

## Coordinates and scale

- Logical cell type/axes: `[for example Vector3i(x, y, elevation)]`
- Tile or module size: `[width × height px | world units]`
- World origin: `[value]`
- Elevation step: `[value]`
- Projection owner: `[resource/node/script path]`
- Picking method and boundary rule: `[method]`

## Assets and footprints

- Ground-contact pivot: `[rule]`
- Visual overhang: `[rule]`
- Gameplay footprint source: `[tile metadata/resource/component]`
- Collision source: `[rule]`
- Supported facings/camera rotations: `[values]`

## Depth and occlusion

- Flat sorting rule: `[rule]`
- Multi-floor/bridge sorting bands: `[rule]`
- Roof/wall reveal behavior: `[rule]`
- World labels/effects layering: `[rule]`

## Movement and navigation

- Input-to-world mapping: `[rule]`
- Navigation implementation: `[AStarGrid2D/custom graph/NavigationRegion3D/etc.]`
- Diagonal movement/corner cutting: `[rule]`
- Height transitions: `[stairs/ladders/drops/links]`
- Dynamic blocker update rule: `[rule]`

## Camera

- Projection/angle: `[value]`
- Rotation policy: `[fixed | permitted steps]`
- Zoom range and pixel-snap policy: `[values]`
- Limits/smoothing/input synchronization: `[rule]`

## Gameplay-size art and readability budget

- Early art-slice review path/revision: `[hero + mechanism states + objective + decor + lighting + HUD]`
- Bulk level authoring blocked until: `[independent PASS condition]`
- Hero minimum bounding-box height or area: `[project-owned threshold]`
- Mean character/background separation: `[metric and threshold]`
- Local-edge separation: `[metric and threshold]`
- Readability capture states: `[quiet | dense | height/lift | route-changing/occlusion]`
- Density/composition capture states: `[start | typical puzzle | densest | highest | objective/result]`

## Validation matrix

- Projection cells: `[negative/origin/positive/elevated samples]`
- Picking boundaries and overlaps: `[cases]`
- Depth-crossing fixtures: `[cases]`
- Navigation and height routes: `[cases]`
- Viewports/zoom/rotations: `[cases]`
- Persistence restore cases: `[cases]`
- Same-frame screenshot/hero-mask reports: `[cases and artifact paths]`
- Independent density/route/silhouette review: `[review path]`

## Performance budgets

- Target device/build: `[value]`
- FPS/frame-time: `[value]`
- Visible cells/props/actors: `[value]`
- Shadow/light/overdraw constraints: `[value]`
- Chunk/streaming policy: `[value]`
