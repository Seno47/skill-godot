# Yandex Games Web Release

Read this only when a Godot Web export targets Yandex Games. SDK behavior and moderation rules can change; re-open the linked official pages before a release instead of treating this file as a frozen copy of the platform manual.

## Record the platform contract first

Before implementation, record:

- archive upload to Yandex hosting or approved custom-domain integration;
- supported orientation, input, minimum embed/viewport range, languages, and size/performance budgets;
- saves: local guest state, Yandex `Player` cloud state, or both, including merge/version policy;
- `ads: none | conservative | aggressive-but-compliant`, plus allowed interstitial breaks, sticky-banner surfaces, and any voluntary rewarded action;
- whether gameplay starts immediately or only after a menu/level selection.

`none` means no game-initiated ad calls; it does not make platform-controlled startup behavior an implementation defect. Do not invent monetization when the user has not authorized it.

## Keep one small SDK bridge

Keep Yandex-specific JavaScript behind a narrow adapter/autoload boundary so gameplay scenes do not call arbitrary browser APIs. Expose semantic operations such as SDK ready, platform pause/resume, gameplay active/inactive, save/load, language, and requested ad transitions. Make a missing SDK in local development an explicit mock/dev state, not an unhandled exception.

For an archive hosted by Yandex, load `/sdk.js` before calling `YaGames.init()`. For a custom domain, use the current absolute SDK URL from the official docs. Prefer the official local development proxy; do not download or package a fake `sdk.js` into the release archive. Inspect both the final `index.html` order and ZIP contents.

Official source: [Connection and usage](https://yandex.com/dev/games/doc/en/sdk/sdk-about).

## Drive lifecycle from real states

Use a small idempotent state machine rather than scattering calls across buttons:

| Game state | Platform action |
|---|---|
| SDK script loaded | call `YaGames.init()` once |
| Engine, first screen, input, and required resources are actually interactive; no loading screen remains | call `ysdk.features.LoadingAPI?.ready()` once |
| Level/play begins or resumes | call `ysdk.features.GameplayAPI?.start()` |
| Menu, pause, result, failure, level end, or pre-ad transition stops active play | call `ysdk.features.GameplayAPI?.stop()` |
| `game_api_pause` | pause simulation/input and mute or suspend game audio |
| `game_api_resume` | restore only the state that was active before the platform pause; do not start gameplay from a menu |

Do not call Game Ready on a timer or immediately after SDK initialization. Verify its actual timing with the debug panel. Subscribe/unsubscribe the same callback references for `game_api_pause` and `game_api_resume`, and test startup-ad, tab-focus, fullscreen-ad, and purchase-like pauses where applicable.

Official sources: [Game loading and gameplay markup](https://yandex.com/dev/games/doc/en/sdk/sdk-game-events), [Pause and resume events](https://yandex.com/dev/games/doc/en/sdk/sdk-events), and [SDK moderation checks](https://yandex.com/dev/games/doc/en/requirements/1/19).

## Save without erasing the guest

- Keep a versioned local save for guests and offline/error fallback.
- When `Player` is available, load cloud data deliberately and reconcile it with local data using an explicit version/timestamp or domain-specific merge rule. Never overwrite newer progress merely because one callback completed last.
- Do not assume authorization or network success. Queue/retry writes within a bounded policy and preserve the playable local state on failure.
- Keep QA seeding separate from both shipping local defaults and cloud data. Test a clean guest, returning guest, authenticated cloud user, offline/error path, and local/cloud conflict if cloud saves are claimed.
- Respect current Player data limits and storage guidance; do not move sensitive authority to an untrusted client save.

Official source: [Player data](https://yandex.com/dev/games/doc/en/sdk/sdk-player).

## Initialize localization from the platform

Use `ysdk.environment.i18n.lang` for the initial automatic language when it is supported, then apply a persisted player override when the game offers manual selection. Define the fallback locale. Verify the debug-panel language mock, reload persistence, every supported translation, numeric/plural forms, placeholder substitution, and narrow-layout overflow.

Official sources: [Environment variables](https://yandex.com/dev/games/doc/en/sdk/defold/environment) and [Debug panel](https://yandex.com/dev/games/doc/en/console/debug-panel). The API object is the relevant contract even when the linked example page uses another engine binding.

## Apply the chosen ad policy

- Request fullscreen ads only at declared natural breaks while gameplay is already stopped. The platform decides whether/frequency to show; a request is not proof of an impression.
- Treat rewarded video as an explicit voluntary exchange with a clear reward. Do not show it when no suitable optional reward exists.
- If sticky banners are controlled through the API, enable the corresponding console mode. Show them only on declared non-gameplay surfaces and hide them during active play when that is the design contract.
- Use platform pause/resume callbacks to keep simulation and audio stopped across ads. Restore the prior game state after close/error rather than blindly starting a level.
- Record `none`, `conservative`, or `aggressive-but-compliant` as a design decision; do not score a different declared policy as a skill defect merely because another game used more or fewer calls.

Official source: [Advertising](https://yandex.com/dev/games/doc/en/sdk/sdk-adv).

## Release evidence and archive gate

Instantiate `assets/yandex-release-checklist.template.md` and `assets/capture-manifest.template.json`. Every checklist row stays `NOT TESTED` until supported by an artifact or named manual observation.

At minimum verify:

- the release-like ZIP has one root `index.html`, valid file names, current size limits, and no local `sdk.js` mock, source captures, seeded saves, or development-only payload;
- the draft/prod environment, not only a local mock, has zero relevant browser-console errors and the debug panel shows correct loader, Game Ready, gameplay, language, focus/pause, and ad transitions used by the game;
- clean and seeded browser profiles are separate and their provenance is in the capture manifest;
- the supported viewport matrix includes the actual orientation plus extreme-narrow, near-square/short-height, and wide cases as applicable;
- onboarding overlays never cover the highlighted target/control; settings overflow scrolls intentionally; localized counts and long strings fit;
- saves, mute/mixer state, focus loss, platform pause/resume, and ads do not duplicate audio, advance simulation, or lose progress.

Official sources: [Testing](https://yandex.com/dev/games/doc/en/console/test-game), [Debug panel](https://yandex.com/dev/games/doc/en/console/debug-panel), and [Draft archive requirements](https://yandex.com/dev/games/doc/en/console/add-new-game/draft).
