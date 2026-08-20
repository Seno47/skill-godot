# Scene-First Architecture

Read this before creating or substantially restructuring Godot scenes.

## Governing distinction

A scene declares composition and initial configuration. A script supplies behavior. Most game concepts need both.

Persist in scenes/resources when a human should be able to open the project and inspect or adjust the result without reading code:

- node hierarchy and reusable scene instances;
- transforms, anchors, layout, draw order, cameras, lights, collisions, navigation, and effect placement;
- exported property values and connections that define authored content;
- meshes, textures, materials, animations, themes, curves, gradients, audio streams, and configuration resources.

Keep in scripts:

- state transitions, input response, movement rules, AI, combat, simulation, save/load, procedural generation, and orchestration;
- focused editor automation that produces persistent scenes/resources;
- calculations that would be brittle or meaningless as serialized data.

## Scene boundary test

Make a concept its own scene when at least one is true:

- it is instantiated more than once;
- it has a meaningful independent identity or lifecycle;
- it combines several nodes that should be edited and tested together;
- designers need to place or configure it as a unit;
- it needs its own animation, collision, audio, effects, or local coordinate space.

Keep a node inline when extraction would create indirection without reuse, ownership, or editing benefit. Scene-first does not mean every node becomes a separate file.

## Prefer composition

- Give a reusable scene a clear root representing its identity, such as `CharacterBody2D`, `Node3D`, `Area2D`, or `Control`.
- Attach behavior near the scene root it governs. Split scripts by responsibility when a root script becomes a miscellaneous service locator.
- Instance reusable scenes inside level/composition scenes.
- Use signals for events crossing component boundaries when that reduces hard references. Use direct calls for clear parent-owned collaborators.
- Use groups for capabilities or broad membership, not as a substitute for explicit ownership.
- Use exported typed references and configuration resources instead of fragile absolute node paths where practical.
- Use autoloads only for services whose identity and lifetime genuinely span scenes. Do not make the whole game depend on a global god object.

## Resources as authored data

Use custom `Resource` types for data with a reusable schema: stats, actions, items, encounters, palettes, spawn tables, dialog definitions, vehicle tuning, or ability definitions. Externalize shared instances as `.tres` so edits propagate intentionally.

Remember that resources are shared by reference. Duplicate them when an instance needs mutable private state; keep runtime state out of shared definition resources unless sharing is intentional.

Use external materials, themes, curves, gradients, and other resources when several scenes must share the same visual language. Keep one-off subresources local when externalization only adds noise.

## Imported scenes

- Treat imported models and other generated imports as source-controlled inputs, not hand-edited Godot scenes.
- Customize imported content through import settings, external materials/resources, inherited scenes, or a wrapper scene.
- Place gameplay scripts, collision overrides, sockets, effects, and project-specific metadata in the wrapper/inherited scene so reimport does not erase them.
- Prefer instancing a 3D imported scene rather than extracting meshes merely to place the object. Extract resources only when independent editing or reuse requires it.

## Direct text editing

Text `.tscn` and `.tres` files are valid authoring surfaces, but they are not arbitrary config files.

Before editing directly:

1. Inspect comparable files created by the project's Godot version.
2. Preserve existing IDs, paths, node parents, connection syntax, and subresource relationships.
3. Use `res://` paths that actually exist. Avoid inventing UIDs.
4. Keep dense transforms, animation tracks, skeletons, imported subresources, and unfamiliar serialized properties editor-authored when practical.
5. Run an editor import after writing and open/run the affected scene.

Never edit `.godot/imported`, `.godot/editor`, or other generated cache data as source.

## Editor automation

Use an `EditorScript`, `@tool` script, or plugin when bulk placement or deterministic authoring is more reliable than hand-writing a large scene file.

- Keep editor-only execution guarded and separate from runtime behavior.
- When adding nodes to an edited scene, set each persistent node's `owner` to the edited scene root.
- Mark the scene unsaved or use editor undo/redo APIs when working interactively.
- Save deliberately and verify the serialized output.
- Avoid destructive tree mutation while the editor is using the affected nodes.
- Remove one-off authoring scripts from the game project after use unless they remain useful tooling.

The generated result must remain a normal editable scene/resource. An authoring generator is not justification for rebuilding the same static tree every time the game runs.

## Runtime construction exceptions

Runtime construction is appropriate for:

- procedural worlds, generated encounters, bullet fields, crowds, pooled transient effects, and streamed data;
- a variable number of objects unknown during authoring;
- performance structures such as `MultiMesh` or servers where a node per element is unsuitable;
- tests and developer-only diagnostic views.

Prefer instantiating authored `PackedScene` objects inside these systems. For procedural content, separate generation data/seed from presentation so results can be reproduced and tested.

## Common failure modes

- A main script creates the camera, player, level geometry, HUD, lighting, and decorations in `_ready()`.
- A scene contains only an empty root whose script is the real level.
- Every object reads and writes one global singleton.
- Dozens of copy-pasted node trees should be scene instances.
- Shared materials or themes are duplicated and drift apart.
- Imported model files are modified indirectly through generated cache files.
- Tool code creates visible nodes without ownership, so they disappear on save.
- A technically reusable architecture leaves no representative composed scene to judge.

Useful official references:

- [Godot best practices](https://docs.godotengine.org/en/stable/tutorials/best_practices/)
- [Running code in the editor](https://docs.godotengine.org/en/stable/tutorials/plugins/running_code_in_the_editor.html)
- [Godot resources](https://docs.godotengine.org/en/stable/tutorials/scripting/resources.html)
