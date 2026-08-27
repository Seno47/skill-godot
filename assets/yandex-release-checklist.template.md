# Yandex Games Release Checklist

- Build/artifact: unrecorded
- Ads decision: none / conservative / aggressive-but-compliant / unrecorded
- Hosting: Yandex archive / custom domain / unrecorded
- Evidence manifest: unrecorded
- Responsibility status: BUILDER_WORK_REMAINING / BUILDER_COMPLETE_READY_FOR_HUMAN_TEST / PUBLICATION_CERTIFIED
- External evidence boundary: none / concise unresolved human-provider-account check

Do not change `NOT TESTED` to `PASS` without an artifact or named manual observation.
Do not translate external `NOT TESTED` rows into a user task list. Builder-owned failures mean continue working; external-only pending rows permit `BUILDER_COMPLETE_READY_FOR_HUMAN_TEST` but not `PUBLICATION_CERTIFIED`.

| Area | Check | PASS / FAIL / NOT TESTED | Evidence |
|---|---|---|---|
| SDK | `/sdk.js` is loaded before `YaGames.init()`; SDK use waits for initialization | NOT TESTED | Unrecorded |
| Ready | `LoadingAPI.ready()` fires once only when the first interactive screen is ready and no loading screen remains | NOT TESTED | Unrecorded |
| Gameplay | `GameplayAPI.start/stop()` match actual level, menu, pause, result, focus, and ad states | NOT TESTED | Unrecorded |
| Pause | `game_api_pause/resume` stop and restore simulation/input/audio without starting gameplay from a menu | NOT TESTED | Unrecorded |
| Saves | Clean guest, returning guest, cloud user/error, and local/cloud merge policy match the declared contract | NOT TESTED | Unrecorded |
| Localization | Initial language uses platform i18n with fallback/manual override; numeric forms and narrow overflow pass | NOT TESTED | Unrecorded |
| Ads | Calls match the recorded policy; rewarded is voluntary; fullscreen occurs only at safe breaks | NOT TESTED | Unrecorded |
| Sticky banner | Console API mode and show/hide surfaces match; banner is absent from active gameplay when declared | NOT TESTED | Unrecorded |
| Audio | Startup ad, fullscreen/rewarded, focus loss, pause, mute, and resume do not leak or duplicate audio | NOT TESTED | Unrecorded |
| Human audio review | A human listener reviewed several minutes of representative target-build gameplay, overlap/repetition, UI, transitions, pause/focus, and settings | NOT TESTED | Unrecorded |
| Profiles | Clean shipping and seeded QA profiles are separate and provenance is recorded | NOT TESTED | Unrecorded |
| Responsive | Declared orientation plus extreme-narrow, near-square/short-height, and wide matrix pass | NOT TESTED | Unrecorded |
| Focus modality | Pointer/touch opening creates no false selected state; keyboard/gamepad opening has visible meaningful focus | NOT TESTED | Unrecorded |
| Overflow | Raw overflow captures show an unclipped focus state and a visible scrollbar/grabber; touch drag changes scroll position | NOT TESTED | Unrecorded |
| Navigation | Large selectors use the recorded scroll/pages/chapters model; all content is reachable and long localized titles remain distinguishable | NOT TESTED | Unrecorded |
| Motion geometry | Hover/focus animation preserves visual center and neighboring container rects unless reflow is intentional | NOT TESTED | Unrecorded |
| Button composition | Localized icon-plus-label groups and icon-only visuals remain centered inside their full hit targets at narrow/wide RU/EN states | NOT TESTED | Unrecorded |
| Pointer click | A full press/release in the Web build emits `pressed`; modality focus cleanup runs only after the button completes its release action | NOT TESTED | Unrecorded |
| Tutorial | Instruction overlay never covers the highlighted target or required control | NOT TESTED | Unrecorded |
| Debug panel | Loader, Game Ready, gameplay, language, focus/pause, and used ad paths pass in draft/prod | NOT TESTED | Unrecorded |
| Browser console | Release-like clean and seeded runs have no relevant errors/warnings | NOT TESTED | Unrecorded |
| Archive | One root `index.html`; current size/name rules pass; local SDK mock, QA state, captures, and dev payload are excluded | NOT TESTED | Unrecorded |
