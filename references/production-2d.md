# 2D Production

Use this for 2D gameplay/world work. Also read the UI guide for interfaces.

## Establish the 2D space

Choose scale and camera behavior from the brief and existing project:

- reference resolution and stretch/aspect behavior;
- world units or pixels-per-unit convention;
- pixel-perfect versus resolution-independent rendering;
- camera zoom, limits, smoothing, drag behavior, look-ahead, shake, and transitions;
- sorting/layering scheme and how actors move through depth;
- target device safe areas and orientation when relevant.

Do not mix arbitrary asset scales and compensate with unrelated node scaling. Avoid fractional transforms for pixel art when they cause unstable sampling.

## Compose native scenes

Typical building blocks include:

- `CharacterBody2D` or another physics body for actors whose motion/collision needs it;
- `Area2D` for detection and interaction volumes;
- `Sprite2D`, `AnimatedSprite2D`, polygons, particles, or custom drawing for presentation;
- `CollisionShape2D`/`CollisionPolygon2D` with shapes chosen for gameplay, not traced visual noise;
- `AnimationPlayer`/`AnimationTree` when animation coordinates several properties or states;
- `AudioStreamPlayer2D`, effect anchors, markers, and scene-instanced attachments;
- `Camera2D` in a deliberate camera rig when behavior exceeds simple following.

Keep the composed node tree visible in the scene. A player scene should expose its visual, collision, interaction, effect, and camera anchors even when scripts drive them.

## Levels and repeated world content

- Use the project's Godot-version-appropriate tile workflow for large grid-authored worlds. In current Godot 4 projects, prefer `TileMapLayer` where supported instead of creating a new deprecated tile setup.
- Keep gameplay collision/navigation metadata in the tile set or authored companion layers when that is maintainable.
- Use reusable scenes for interactive objects whose behavior and visuals exceed a tile.
- Separate background, gameplay, foreground/occluder, effects, and debug layers intentionally.
- Use parallax because it supports depth and motion, not as automatic decoration.
- Break very large worlds into authored chunks/rooms when streaming, collaboration, or editor performance requires it.

## Animation and feedback

- Establish pivots and attachment points before creating animation variants.
- Keep frame-based sprite animation on a consistent grid and inspect every frame in context.
- Use `AnimationPlayer` for authored timing across transforms, modulate, audio, particles, hitboxes, or UI; use state machines when transitions genuinely need them.
- Make gameplay timing authoritative in gameplay logic when animation playback can vary. Synchronize through explicit events rather than fragile frame guesses.
- Layer anticipation, impact, recovery, particles, camera response, sound, and hit-stop only to the degree appropriate to the user's motion direction.

## Lighting and materials

- Use 2D lights, occluders, normal maps, canvas modulation, particles, and shaders as a coherent lighting system.
- Check render method/platform limitations before relying on expensive lights or screen-reading shaders.
- Preserve value readability without effects enabled; lighting should strengthen hierarchy rather than rescue indistinct assets.
- Avoid applying one global shader treatment to incompatible assets and calling the result cohesive.

## Physics and navigation

- Configure collision layers/masks according to explicit gameplay categories.
- Use simple stable collision shapes for moving objects; reserve complex polygons for suitable static geometry.
- Keep visual and collision transforms aligned and inspect debug collision output during play.
- Build navigation regions/obstacles for the actual movement model and agent size. Test narrow passages and dynamic changes.
- Make fixed-timestep movement and acceleration behavior independent of rendering frame rate.

## 2D visual completion gate

Inspect screenshots and motion at representative states:

- spawn/idle, traversal, interaction/combat, damage/failure, and success/transition as applicable;
- quiet and visually dense parts of a level;
- intended window/aspect extremes;
- foreground/background overlap and camera limits;
- effects at full action intensity.

Reject the pass if sprites clash in pixel density or perspective, actors disappear into backgrounds, collisions visibly disagree with art, tiles repeat mechanically without intent, or default shapes remain in a state described as final.

Useful official references:

- [Godot 2D documentation](https://docs.godotengine.org/en/stable/tutorials/2d/)
- [2D movement overview](https://docs.godotengine.org/en/stable/tutorials/2d/2d_movement.html)
- [2D navigation overview](https://docs.godotengine.org/en/stable/tutorials/navigation/navigation_introduction_2d.html)
