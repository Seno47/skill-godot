# XR and Console Delivery

Read only when XR hardware or a console platform is explicitly in scope.

## XR

Declare runtime/API, headset and controller profiles, tracking origin, standing/seated/room-scale mode, locomotion/turning/teleport options, recenter, dominant hand, interaction reach, world scale, frame-time target, stereo rendering limits, boundary/guardian assumptions and comfort settings. Test actual hardware for tracking loss/recovery, controller loss, recenter, pause/system overlay, floor height, hand identity, near clipping, text legibility, motion comfort and sustained performance. A desktop mirror capture cannot certify stereo depth, tracking or comfort.

OpenXR must be initialized through the intended startup path and not repeatedly across scene changes. Prefer the renderer supported by the actual device/performance target; independently verify effects and shaders in stereo.

## Consoles

Godot console delivery requires authorized platform access, SDKs and an approved port/export provider or a substantial custom port. Do not invent proprietary certification rules, credentials or devkit results. Record only user-authorized platform requirements and mark unavailable NDA material/devkit testing as blocked, not inferred. Verify package identity, save/user/controller lifecycle, suspend/resume, sign-in changes, storage/full/error paths, achievements/services and performance on the real target.

Use `assets/xr-console-review.template.md` and select the XR or console rubric modifier honestly.

Primary Godot references:

- [Setting up XR](https://docs.godotengine.org/en/stable/tutorials/xr/setting_up_xr.html)
- [Custom platform ports](https://docs.godotengine.org/en/stable/engine_details/engine_api/custom_platform_ports.html)
