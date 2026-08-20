# Memory, Loading, and Stutter

Read this only for RAM/VRAM pressure, leaks, scene transitions, startup/loading time, streaming, shader hitches, or long-session stability.

## Separate the budgets

Measure independently:

- steady and peak system RAM;
- steady and peak VRAM by resource/category;
- cold startup and warm startup;
- level/scene transition time and longest main-thread stall;
- long-session memory trend after repeated enter/exit cycles;
- shader/pipeline compilation spikes versus file/resource loading;
- concurrent loaded world chunks and largest resource groups.

Use the target export, renderer, resolution, quality preset, and hardware. A small PCK can still use excessive RAM/VRAM; a fast average frame can still freeze on synchronous load.

## Resource lifetime first

- Identify who holds references across scene changes: autoloads, caches, signals/callables, arrays/dictionaries, static state, retained scenes, viewports, audio, navigation, and custom managers.
- Distinguish shared immutable definition resources from mutable runtime state.
- Release or bound caches intentionally; do not rely on scene changes to free objects still referenced globally.
- Compare memory before load, after load, after unload, and after repeating the cycle.
- Use Godot Monitors/Video RAM and version-appropriate object/memory profiling. ObjectDB Profiler exists only in newer Godot versions and does not cover all native/external memory.
- Do not add pooling when the pool itself retains excessive resources or when allocation is not the bottleneck.

## Loading strategy

- Use ordinary `load`/preload for small predictable resources whose synchronous cost is acceptable.
- Use `ResourceLoader.load_threaded_request`, status/progress checks, and `load_threaded_get` for heavy resources that can begin before they are needed. Calling `load_threaded_get` too early can still block.
- Keep loading UI responsive and report honest progress when available.
- Stage dependencies needed for the next scene instead of preloading the entire game into an autoload.
- Stream/chunk large worlds by spatial/gameplay relevance with explicit ownership, cancellation, and unload boundaries.
- Avoid spawning a huge imported scene, rebuilding navigation, compiling many shaders, and starting all audio on the same frame.
- Precompute/bake expensive static data when it meaningfully shifts work out of interactive frames.

Threaded loading does not make every resource safe for arbitrary cross-thread mutation. Keep scene-tree and rendering operations on supported threads and follow the project's Godot-version rules.

## VRAM and asset residency

- Inspect actual imported formats and VRAM usage, not compressed source-file size.
- Right-size textures for their maximum screen use; configure mipmaps/compression/platform overrides deliberately.
- Avoid keeping every high-resolution variant, viewport target, cubemap, lightmap, animation texture, or unused material resident.
- Reuse compatible resources while avoiding giant atlases/materials that force unrelated content to remain resident.
- Budget render targets, MSAA, shadows, GI, post-processing, particles, and viewport resolution because their memory may scale with resolution rather than source files.

## Pipeline and first-use stutter

Determine renderer and Godot version before applying a workaround:

- Godot 4.4+ Forward+/Mobile can precompile many pipelines when meshes/nodes/features are loaded or instanced; monitor pipeline categories to find first-use gaps.
- Dynamically introduced effects may need to be instantiated during a loading phase when measurements show first-use pipeline spikes.
- Compatibility lacks the modern ubershader/pipeline-precompile path and may require legacy material/effect warm-up.
- Shader baking in newer versions can reduce first startup shader work but increases export time and PCK size and is renderer/platform/headless constrained.

Do not create a giant hidden “warm-up scene” without measuring its startup, RAM, VRAM, and package tradeoffs.

## Validation gate

Run repeatable cold/warm load and repeated unload cycles. Record peak/steady RAM and VRAM, transition times, worst stall, pipeline spikes, loaded chunk counts, and device/build settings. Confirm cancellation/error paths, no unbounded growth, no visible missing dependencies, and no new startup/package regression hidden by improved gameplay loading.

Official references:

- [Background loading](https://docs.godotengine.org/en/stable/tutorials/io/background_loading.html)
- [Debugger monitors and Video RAM](https://docs.godotengine.org/en/stable/tutorials/scripting/debug/debugger_panel.html)
- [Pipeline compilation stutter](https://docs.godotengine.org/en/stable/tutorials/performance/pipeline_compilations.html)
- [ObjectDB profiler](https://docs.godotengine.org/en/stable/tutorials/scripting/debug/objectdb_profiler.html)
