# UI Reference Integration

Read this when the user supplies an approved screenshot, mockup, design export, or existing game screen that the Godot UI must reproduce. A visual reference is a measurable target, not permission to flatten the interface into one bitmap or rebuild ordinary controls in code.

## Lock the target

Before implementation, record:

- the exact approved source file, pixel size, crop, scale, language, UI state, and intended viewport;
- which regions are exact targets, which are inspirational, and which may change for usability/localization;
- target platforms, orientation, safe areas, input modalities, and supported viewport extremes;
- the screen's hierarchy, key bounding boxes, alignment lines, spacing rhythm, type roles, component states, and distinctive art;
- named deviations required by gameplay, accessibility, localization, or unavailable licensed assets.

Do not claim parity with an ambiguous mood board. Select one controlling reference per screen/state or document how references divide responsibility.

## Convert the reference into native authored UI

For each formal screen:

1. Create a distinct `.tscn` screen or reusable widget scene when it has its own identity/lifecycle.
2. Make its formal hierarchy visible and editable in the editor before `_ready()` runs. Scripts may populate dynamic data and state, but must not manufacture the ordinary screen tree.
3. Map reference regions to `Container`, `Control`, `Theme`, `StyleBox`, font, icon, texture, and animation resources.
4. Use real localized text and native controls for actions, values, input, focus, accessibility, and dynamic content.
5. Use `NinePatchRect`/`StyleBoxTexture`, atlases, or isolated artwork only where the reference actually requires texture-based framing. Preserve corner/edge behavior at every supported size.
6. Keep decorative children mouse-filtered so the authored interactive shell owns the hit target and focus state.
7. Preserve distinctive shapes. Do not translate every irregular tab, carved frame, leaf, weapon, badge, or dial into the same generic rounded rectangle.

If the approved reference itself is inaccessible, misleading, or unusable at the target size, record the conflict and obtain a decision rather than silently changing the design while still claiming parity.

## Prove runtime parity

Capture the implemented screen in the same language, state, viewport, crop, and pixel dimensions as the reference. Compare:

- side by side for hierarchy and semantics;
- a 50% overlay for position, scale, and shape drift;
- an absolute diff for unexpected changed regions;
- responsive states separately rather than resizing the reference and declaring success.

The bundled diagnostic helper creates these artifacts:

```bash
python <skill-dir>/scripts/image_compare.py \
  --reference <approved.png> \
  --actual <runtime.png> \
  --output-dir <reports/ui-parity> \
  --summary --json-output <reports/ui-parity.json>
```

Use error thresholds only for stable deterministic captures. Pixel metrics are diagnostic, not a design verdict: font rasterization, renderer differences, animation, particles, and antialiasing can increase the diff while the composition is correct. Conversely, a low global error can hide a displaced small primary action. Review named regions and the raw images.

For localized screens, capture at least one short and one long representative locale. For input-dependent screens, capture pointer/touch and keyboard/gamepad focus states separately. For responsive screens, apply the viewport matrix in `visual-validation.md` and record intentional reflow.

Complete `assets/ui-reference-parity.template.md`. A strict-parity claim fails when the target artifact, capture conditions, raw comparison images, or named deviations are missing.

## Integration traps

- A full-screen background screenshot is not a functional UI implementation.
- Baking labels into images breaks localization, text scaling, accessibility, and dynamic state.
- Exact coordinates at one viewport do not prove responsive layout.
- A screen that only becomes recognizable after `_ready()` has hidden its composition from the editor.
- Matching palette alone does not match hierarchy, spacing, typography, silhouettes, or interaction states.
- Reusing one generic button scene for visually distinct reference components may reduce maintainability rather than improve it.
- A diff created from different crops, DPI scales, fonts, animation frames, or seeded state is not comparable evidence.

Useful primary references:

- [Godot Control nodes and GUI](https://docs.godotengine.org/en/stable/tutorials/ui/)
- [Using containers](https://docs.godotengine.org/en/stable/tutorials/ui/gui_containers.html)
- [Introduction to GUI skinning](https://docs.godotengine.org/en/stable/tutorials/ui/gui_skinning.html)

