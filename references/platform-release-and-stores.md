# Desktop, Mobile, and Store Release

Read this when producing a distributable Windows/Linux/macOS/Android build or integrating a desktop/mobile storefront. Apply [export-and-size.md](export-and-size.md), [save-data-integrity.md](save-data-integrity.md), and [input-and-accessibility.md](input-and-accessibility.md). Use the Yandex guide for that platform rather than duplicating it here.

## Record the release matrix

Instantiate `assets/platform-release-matrix.template.md`. For each declared platform/store record exact Godot/export-template version, renderer/architecture, preset, package type, signing/notarization state, SDK/addon and version, required runtime/permissions, storage/cloud paths, input devices, display/safe-area lifecycle, achievements/stats/leaderboards/overlay/entitlement policy, crash reporting, upload artifact and store-side tests.

An exported file is not release evidence. Install or deploy the exact candidate through the closest available production path and test first launch, update over a previous version, uninstall/reinstall retention policy, offline start, missing store client/service, account change, overlay/focus, suspend/resume, display/DPI/fullscreen changes, input hot-plug, save/cloud conflict, achievement/reward idempotence, crash/log location and clean exit.

## Keep platform code optional and bounded

Wrap store services behind small project-owned interfaces. Gameplay must have an explicit response when the SDK is absent, initialization fails, the user is offline, entitlement is unavailable, overlay pauses input, cloud quota/conflict occurs, or an achievement call retries. Do not make the editor mock look like production success.

Keep signing credentials, API secrets and upload tokens outside the project/PCK and reports. Record plugin provenance, supported Godot/platform versions, permissions, native binaries and export filters. Store achievements/leaderboards require exact configured IDs and readback; method success alone is not portal configuration proof.

Godot desktop exports require the appropriate release preset/template; Windows supports export-time code signing when configured. Android release needs the intended release signing identity and device/track verification. Steam features such as Cloud, Input, achievements, Workshop and matchmaking are optional product choices, not a default checklist—enable and verify only those in the brief.

Primary references:

- [Godot exporting projects](https://docs.godotengine.org/en/stable/tutorials/export/exporting_projects.html)
- [Godot exporting for Windows](https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_windows.html)
- [Steamworks features](https://partner.steamgames.com/doc/features)

