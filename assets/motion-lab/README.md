# Editable motion mechanisms

This small Godot 4 project is a teaching fixture, not a game template or finished artwork. Its four cells demonstrate immediate press response with stable hit targets, a reward arc, an authored work/contact event, tangent-facing travel and an interruptible panel. The restrained shapes make defects observable; adapt the principles to the chosen game's own art.

Run with the project-compatible Godot binary:

```
godot --path <skill>/assets/motion-lab --headless -- --self-test
godot --path <skill>/assets/motion-lab --headless -- --self-test --broken
godot --path <skill>/assets/motion-lab --headless -- --self-test --reduced-motion
```

The deliberately broken case must exit 1 for off-center press response, sideways travel and missed work contact. A failure in that command is the expected regression result.

For raw render evidence use an offscreen-capable renderer (not headless, which cannot produce real screenshots):

```
godot --path <skill>/assets/motion-lab --write-movie <output>/reference.avi --fixed-fps 30 --quit-after 240 -- --capture
godot --path <skill>/assets/motion-lab --write-movie <output>/negative.avi --fixed-fps 30 --quit-after 240 -- --capture --broken
```

Eight seconds at 30 FPS bounds capture cost. Decode with `scripts/mjpeg_avi_watchback.py` and inspect at normal speed. Retain timestamps when turning, contact or response looks wrong. Automated PASS proves dispatch/settlement/contact contracts only; it does not certify motion taste, professional vehicle animation, responsive UI or final production graphics.

The motion source, curves, anchors and persistent visuals are in `lab.tscn`; `lab.gd` controls state and dynamic endpoints. Use the related production guides for skeletal animation, wheel/foot contact, crowds, camera and audio. Do not copy diagnostic headings or test controls into a shipping game.
