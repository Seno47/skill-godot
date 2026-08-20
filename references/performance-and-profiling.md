# Performance and Profiling

Read this only for FPS, CPU/GPU/physics bottlenecks, large instance counts, target-device budgets, performance regressions, or release profiling. Do not apply optimization folklore without measurements.

## Define the performance contract

Record the conditions that make results comparable:

- target hardware/device class and operating system;
- Godot version, renderer, graphics API, quality preset, and build type;
- resolution/window size, V-Sync/frame cap, and physics tick rate;
- representative scene, camera path, actor/object count, and gameplay state;
- target FPS/frame budget and tolerated spike percentiles;
- whether profiling overhead is enabled.

Frame budgets:

| Target | Total frame time |
| --- | ---: |
| 30 FPS | 33.33 ms |
| 60 FPS | 16.67 ms |
| 90 FPS | 11.11 ms |
| 120 FPS | 8.33 ms |

Use average/median for throughput and p95/p99/max for stutter. A stable empty scene or five-frame headless smoke test is not a performance benchmark.

## Measure before changing

1. Warm up the representative flow where caches/pipelines normally warm up.
2. Capture a repeatable baseline on the target or weakest representative device.
3. Classify the limiting domain: scripting/CPU, physics/navigation, render CPU/draw submission, GPU/fill/shaders, allocation/GC, audio, loading, or external/system work.
4. Use Godot Profiler for script/engine categories, Visual Profiler for render CPU/GPU, Monitors for runtime counts, Video RAM for VRAM resources, and platform/external profilers when needed.
5. Form one falsifiable bottleneck hypothesis, change the smallest relevant cause, and rerun the same scenario.
6. Keep the change only when measurements improve enough to justify maintenance/quality cost and no target regresses.

Profile release-like builds too. Debug/editor results help diagnosis but do not replace target export measurements. Keep resolution and quality constant when comparing GPU results.

Use a bounded `run` for profiling unless a visual recording is itself required. Godot `--write-movie` can produce a very large AVI or image sequence in seconds and adds capture overhead, so it is not a performance-measurement default. When a movie is required, bound frames and resolution, write to a known disposable/report path, monitor free space/output size, and delete or archive it deliberately after review.

## CPU, scripts, and scene tree

Investigate measured hot paths and excessive call counts before changing language or architecture.

- Avoid per-frame work that can be event-driven, amortized, spatially limited, cached, or updated less frequently.
- Disable processing for inactive/offscreen/distant systems when behavior allows; hiding a node alone may not stop processing.
- Reduce repeated tree searches, transient allocations, string work, conversions, and rebuilding arrays/dictionaries in hot loops when profiling implicates them.
- Separate large simulations from one-node-per-element designs when node/process overhead is the measured constraint; use data-oriented storage or server APIs only when warranted.
- Pool objects when allocation/free or GC spikes are demonstrated and lifecycle complexity remains manageable—not by default.
- Move proven heavy computation to threads, C#, GDExtension, compute, or precomputation only after the algorithm/data model is sound and thread/portability costs are justified.

## Physics and navigation

- Use gameplay-appropriate simple collision for moving bodies; avoid render-detail collision.
- Limit active bodies/areas/queries to the relevant world region.
- Avoid rebuilding navigation maps, meshes, avoidance state, or complex queries every frame without need.
- Treat physics tick-rate changes as a design/input/feel decision, not a free optimization. Validate interpolation, latency, determinism, and collisions.
- Test worst-case contact, crowd, projectile, and moving-platform scenarios relevant to the game.

## GPU and rendering

Use measured render/GPU evidence and the active renderer:

- reduce expensive state/material/shader variation when draw submission is limiting;
- share meshes/materials and use instancing appropriately;
- use `MultiMesh` for very large repeated visual sets only when per-instance nodes/behavior/culling are unnecessary or spatially chunked;
- apply LOD/visibility ranges/occlusion/impostors where distance and camera make them effective;
- reduce overdraw, transparent layers, full-screen effects, screen-reading shaders, particle fill, and large blended sprites when fill rate is limiting;
- budget dynamic lights, shadows, GI, reflection probes, decals, skinning, morphs, and viewport rendering by target platform;
- reduce resolution or use scaling only when it addresses a GPU-bound workload and visual loss is accepted.

Automatic/manual instancing, pipeline behavior, and available profiler categories vary by Godot version and renderer. Verify against the actual project version.

## Regression evidence

Store or report:

- exact scenario/config/device/build;
- baseline and new median/p95/p99 frame time;
- CPU/GPU/physics breakdown and relevant counts;
- visual/behavior tradeoffs;
- files/settings changed;
- remaining bottleneck.

Use `scripts/performance_budget.py` to compare measurement JSON with project budgets. Do not fabricate metrics when automated capture is unavailable.

Keep the project-specific metric names, but make direction explicit in the budget:

```json
{
  "schema_version": 1,
  "profiles": {
    "desktop-low": {
      "metrics": {
        "fps_p95": {"min": 60, "unit": "FPS", "regression_percent_max": 5},
        "frame_ms_p99": {"max": 20, "unit": "ms"}
      }
    }
  }
}
```

Measurements use the same profile and metric keys with numeric values. Run a compact gate while preserving the full result:

```bash
python scripts/performance_budget.py --budget performance-budget.json --measurements current.json --baseline previous.json --summary --json-output performance-report.json
```

## Validation gate

An optimization is complete only when the same representative scenario improves on target hardware/build, p95/p99 do not hide new spikes, behavior/visual quality remains acceptable, memory/loading/build size regressions are checked where relevant, and the result is repeatable across more than one run.

Official references:

- [General optimization tips](https://docs.godotengine.org/en/stable/tutorials/performance/general_optimization.html)
- [Debugger panel and profilers](https://docs.godotengine.org/en/stable/tutorials/scripting/debug/debugger_panel.html)
- [CPU optimization](https://docs.godotengine.org/en/stable/tutorials/performance/cpu_optimization.html)
- [GPU optimization](https://docs.godotengine.org/en/stable/tutorials/performance/gpu_optimization.html)
- [MultiMesh tradeoffs](https://docs.godotengine.org/en/stable/tutorials/performance/using_multimesh.html)
