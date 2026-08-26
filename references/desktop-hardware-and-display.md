# Desktop hardware and display

Use this guide for Windows/macOS/Linux releases, especially when minimum hardware, multiple renderers, ultrawide/HiDPI, HDR, multiple displays, or controller hot-plug are promised. Virtual resolutions and editor previews do not replace real machines.

## Matrix before final optimization

Record minimum, representative, and optional high profiles: OS build, CPU/GPU class, RAM/VRAM, renderer/driver, display layout/DPI/refresh/HDR, input devices, resolution/performance budget, and whether each is a real machine. Instantiate `assets/desktop-hardware-contract.template.json`.

Prove exact-candidate clean launch plus windowed resize, fullscreen/borderless toggles, minimum size, ultrawide, high-DPI/4K scaling, multi-monitor placement, alt-tab/focus recovery, monitor disconnect/reconnect, controller hot-plug, and low-VRAM/fallback behavior. Check that UI remains legible/onscreen, materials and post-processing survive the renderer, settings persist, input capture recovers, and window placement cannot strand the game offscreen. Gate HDR only if promised and validate SDR fallback.

Run `scripts/desktop_hardware_probe.py` for budgets and coverage. A human must play representative gameplay on the real minimum and representative profiles and record feel/stutter/readability in `assets/desktop-hardware-review.template.md`; averages and simulated limits cannot certify the hardware claim.

## Primary references

- [Godot multiple resolutions](https://docs.godotengine.org/en/latest/tutorials/rendering/multiple_resolutions.html)
- [Godot resolution scaling](https://docs.godotengine.org/en/stable/tutorials/3d/resolution_scaling.html)
- [Godot HDR output](https://docs.godotengine.org/en/stable/tutorials/rendering/hdr_output.html)
