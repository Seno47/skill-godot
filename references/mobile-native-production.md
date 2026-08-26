# Mobile-native Production

Read this for Android/iOS delivery beyond a browser wrapper.

Record minimum OS/device classes, renderer, orientation policy, safe-area/cutout behavior, touch and controller support, frame/memory/package/startup budgets, thermal/battery session target, permissions, background/suspend/resume, audio interruption, offline behavior, storage/save migration, billing/entitlement choices, privacy declarations and store tracks.

Test physical low/mid/high representatives when promised; desktop emulation cannot certify touch latency, cutouts, OS gestures, thermal throttling, background eviction, memory pressure, audio routing, permissions or purchase lifecycle. Keep critical controls out of cutouts and system-gesture regions and preserve state through rotation only when orientation changes are supported.

Use `assets/mobile-native-review.template.md`. Evidence includes cold/warm start, install/update, interrupted download if relevant, airplane mode, permission denied/revoked, background/restore, incoming audio interruption, low storage/memory, thermal soak, safe-area screenshots, touch targets, controller hot-plug, purchase retry/restore where enabled, and clean uninstall/reinstall expectations.

Primary Godot references:

- [Overview of renderers](https://docs.godotengine.org/en/stable/tutorials/rendering/renderers.html)
- [GPU optimization](https://docs.godotengine.org/en/stable/tutorials/performance/gpu_optimization.html)
