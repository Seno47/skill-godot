# Input, Local Multiplayer, and Accessibility

Read this for remapping, multiple controllers, local co-op, touch, input glyphs, accessibility options, subtitles, assist modes, or more than one supported modality. A populated Input Map and visible settings screen do not prove usable input.

## Declare the supported matrix

Start from `assets/input-accessibility-contract.template.json`. Record required devices/modalities, critical actions, simultaneous-player count, controller ownership/join policy, supported remapping conflicts, glyph families, touch target/dead-zone/sensitivity budgets, focus policy, accessibility features, persistence, and unsupported combinations.

Use semantic actions rather than hard-coded physical keys. Keep mouse-look, stick-look, touch gestures and cursor/focus navigation as distinct input shapes even when they feed one gameplay intent. Do not infer controller layout from one generic USB device name; display the glyph family actually detected or provide a safe generic fallback.

## Remapping and device lifecycle

Prove each critical action remains reachable after remap and reset. Handle duplicate/conflicting bindings with an explicit policy; never let the user remove the only menu-back/confirm path without a recovery route. Persist bindings by stable action/event data and migrate them when actions change.

For local multiplayer, assign devices to player slots deliberately. Test join/leave, one keyboard policy, two identical controllers, hot-plug/reconnect, pause ownership, focus loss, disconnected required player, shared versus split camera, and per-player UI/audio identity. A global `Input.is_action_pressed()` path can accidentally drive every player.

## Accessibility is behavior

Only expose settings that have a verified effect. As applicable test:

- text/UI scale, subtitle size/background/speaker and critical non-dialog captions;
- reduced motion/flashes/shake and photosensitivity-safe alternatives;
- color-independent state cues and contrast under representative filters;
- hold/toggle alternatives, repeated-input reduction, timing assists and pauseability;
- aim/steering assistance without hidden competitive advantage across modes;
- mono/downmix and separate master/music/SFX/dialog controls;
- touch target size/spacing, gesture alternatives, safe areas and orientation;
- screen-reader or spoken UI only when genuinely supported and tested.

Run:

```bash
python <skill-dir>/scripts/input_accessibility_probe.py --model reports/input-accessibility-contract.json --summary --json-output reports/input-accessibility-audit.json
```

The probe checks required device/action coverage, remap/reset/persistence, conflicts and emergency navigation, glyph truth, hot-plug/local-player ownership, modality switching, and declared accessibility-effect traces. Complete `assets/input-accessibility-review.template.md` for an independent target-build review; a checklist cannot establish comfort or comprehension.

Primary Godot references:

- [Using InputEvent](https://docs.godotengine.org/en/stable/tutorials/inputs/inputevent.html)
- [Controllers, gamepads, and joysticks](https://docs.godotengine.org/en/stable/tutorials/inputs/controllers_gamepads_joysticks.html)

