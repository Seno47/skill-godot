# Runtime Authoring Tools

Read this for in-game level editors, quest/dialogue builders, scenario tools, mod kits or any creator-facing workflow shipped outside the Godot editor.

Model edits as stable versioned commands over validated data, not ad-hoc scene mutation. Define document IDs, schema/migrations, ownership, selection/manipulation rules, snapping, constraints, undo/redo transactions, autosave/recovery, preview/playtest isolation, validation severity, publish/export packaging, dependency tracking and compatibility with game saves/mod manifests.

Every command must be reversible or explicitly non-undoable before execution. Compound gestures produce one coherent undo step; undo/redo cannot duplicate registrations, rewards, signals or resource ownership. Runtime `UndoRedo` can implement action history, but the project still owns serialization, validation and destructive-operation UX.

Use `assets/runtime-authoring-review.template.md`. Test clean creation, edit/undo/redo, multi-select/bulk edit, copy/paste, invalid placement, delete referenced object, save/reload, crash recovery, old-document migration, preview isolation, publish/reimport, missing dependency, keyboard/controller/touch paths as promised, and an uncoached creator session.

Primary Godot reference: [UndoRedo](https://docs.godotengine.org/en/stable/classes/class_undoredo.html).
