# Large Worlds and Streaming

Read this for open worlds, seamless regions, planetary/space scale, very high speeds, persistent streamed zones, runtime terrain or long traversal without loading screens.

Choose coordinates from measured scale: ordinary single precision, authored zones centered near origin, origin shifting, or a double-precision Godot build. Large-world coordinates carry CPU/memory/platform costs and are not a substitute for streaming. Record world/zone/chunk IDs, coordinate conversion, ownership, load radius and hysteresis, memory residency budget, navigation/physics/audio/VFX activation, save ownership, and multiplayer handoff if applicable.

Background loading is only nonblocking while retrieval waits for a completed request; prove actual frame-time behavior at boundary crossings. Stage data, resources, nodes, navigation, physics and presentation deliberately, and cancel/de-duplicate obsolete requests. Unloading must preserve durable state, detach signals/timers, release references and never orphan targets or duplicate rewards.

Use `assets/large-world-streaming-review.template.md`. Target-build evidence covers repeated forward/back crossings, teleport/fast travel, rapid direction reversal, save/load at a boundary, death/restart, lowest-memory target, highest-speed traversal, missing/corrupt chunk recovery and a long residency/leak loop.

Primary Godot references:

- [Background loading](https://docs.godotengine.org/en/stable/tutorials/io/background_loading.html)
- [Large world coordinates](https://docs.godotengine.org/en/stable/tutorials/physics/large_world_coordinates.html)
