# Assistive accessibility

Use this guide when the release promises screen-reader/non-visual access, full keyboard or switch-like operation, captions for critical audio, low-vision support, or deeper motor/cognitive assists. It extends—not replaces—the input/accessibility and UI guides.

## Semantic and behavioral contract

Record target platforms, actual assistive technologies, critical flows, accessible names/descriptions/roles/states/values/actions, navigation order, dynamic announcements, focus restoration, non-color cues, caption policy, motion/timing/cognitive assists, and test owners. Instantiate `assets/assistive-accessibility-contract.template.json`.

Set Godot `Control` accessibility metadata from the authored meaning, not the visual filename. Decorative nodes stay out of the accessibility flow. Compound/custom controls expose one coherent role/name/value/action. Dynamic gameplay announcements are prioritized, interruptible, and bounded; do not narrate every frame. All critical flows must work without pointer precision, without color alone, and with the promised timing/motion assists actually changing behavior.

## Evidence

Run the exact candidate through menu, settings, onboarding, gameplay, pause, result, live-region updates, keyboard-only, gamepad-only, reduced motion, non-color and subtitle/caption states. `scripts/assistive_accessibility_probe.py` checks semantic/behavioral coverage, but an accessibility tree dump is structural evidence only. The human gate in `assets/assistive-accessibility-review.template.md` requires the real platform screen reader/assistive technology and representative users or an appropriately qualified accessibility reviewer; the user commissioning the game is not the default routine tester.

Do not promise platform accessibility unsupported by the selected Godot/platform path. Record the exact engine/platform limitations and provide an honest alternative where possible.

## Primary references

- [Godot AccessibilityServer](https://docs.godotengine.org/en/stable/classes/class_accessibilityserver.html)
- [Godot Control accessibility properties](https://docs.godotengine.org/en/stable/classes/class_control.html)
- [Godot GUI keyboard/controller navigation](https://docs.godotengine.org/en/latest/tutorials/ui/gui_navigation.html)
