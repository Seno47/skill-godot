# Audio, VFX, and Fonts

Read this for sound effects, music, voice, fonts, particles, shaders, trails, decals, and other effects. These assets need the same provenance and integration discipline as images/models.

## Set the audio delivery bar

Match the audio obligation to the requested deliverable:

- A focused system change only needs the audio it affects. A non-production prototype may use clearly labeled temporary audio when testing the mechanic requires it.
- A complete game, autonomous build, or vertical slice needs coherent production SFX, suitable music or intentional ambience/silence, mixer controls, saved settings, and runtime verification unless the user explicitly requests a silent experience.
- A file existing under `res://` or an `AudioStreamPlayer` node is not evidence of finished sound. Audio must fit the action, world, presentation, mix, platform, and repetition rate in the actual game.

Do not call a full playable result complete while its sound is still generic placeholder material.

## Define sonic direction before collecting files

Derive a compact sonic direction from the game's world, material language, scale, perspective, tempo, and interaction priorities. Record it beside the visual direction so sourcing and integration use one target. Include:

- physical/material sources, perceived scale, camera/listener perspective, and acoustic space;
- tonal versus noisy character, frequency/detail density, dynamics, tempo, and intensity range;
- the function of music, ambience, UI sound, voice, and silence in each representative state;
- reference qualities and explicit exclusions without requesting imitation of a copyrighted track or identifiable performer;
- whether generative audio is permitted; absent explicit permission, treat it as opt-in and prefer human-recorded, human-composed, or manually designed sources.

Create a small sound-event map for the slice: event/state, gameplay priority, intended source/material, variation need, spatial behavior, bus, and implementation owner. Cover must-hear feedback first—core action, impact/collection, danger, success/failure, and essential UI confirmation as applicable. Do not sonify every event merely to make the project seem polished.

## Reject audio slop and placeholders

- Do not create final WAV/OGG files by writing simple oscillator, noise, or arpeggiator formulas merely to satisfy an audio requirement.
- Reject generic sine/square `beep-boop`, one default UI click used everywhere, arbitrary whoosh/pop layers, and unrelated stock music unless that exact vocabulary belongs to the accepted sonic direction.
- Do not disguise one sample as a complete library by pitching it across unrelated actions. Controlled pitch/volume/sample variation is useful within one coherent event family, not as a substitute for distinct source material.
- Procedural tones, chiptune synthesis, and deliberately minimal UI sounds are valid only when the brief establishes that aesthetic and the result still has intentional timbre, envelope, hierarchy, variation, and mix.
- Generative music, SFX, or voice is not the default fallback for missing assets. Use it only with user permission, disclose it in the manifest, and reject obvious model artifacts or stylistic drift. Never imply that generated origin or a plausible waveform makes an asset shippable.
- Prefer targeted foley/recording, manually layered and edited licensed recordings, or human-composed music that fits the event map. Search by physical source, action, intensity, distance, environment, duration, loop behavior, and perspective—not by a generic noun alone.

Verify the exact license for recordings, music, samples, voices, and generated output. Sample libraries may restrict isolated redistribution even when use in a finished game is allowed. Record performer/author, source, license, attribution, generation tool/voice, and consent/identity constraints where relevant. Do not imitate a living performer or identifiable person without appropriate authorization.

## Design SFX as feedback

- Make high-priority sounds describe cause and material. Layer transient, body, texture, and tail only when those layers improve the event; a small action does not need trailer-scale impact design.
- Provide controlled variants for frequent events and context variants for materially different surfaces, intensities, distances, weapons, or outcomes.
- Align audible attack and impact with animation/gameplay timing. Avoid pre-delay that makes input feel late or long tails that mask the next decision.
- Preserve contrast. Important actions should remain identifiable when common events overlap; ambience and music should leave spectral and dynamic room for them.
- As a listening check, ask whether the core action and result can be distinguished without looking at the screen. This is a quality signal, not a reason to duplicate every visual event in sound.

## Audio preparation and Godot integration

- Preserve clean source files when future editing matters; export runtime formats appropriate to short samples versus streamed music/ambience.
- Trim silence, remove clicks/DC problems, create intentional fades and seamless loops, and keep a consistent loudness/dynamic-range approach.
- Choose mono for positionable sounds when stereo width would fight spatialization; keep intentional stereo for music/ambience/UI where appropriate.
- Route playback through named audio buses for music, ambience, SFX, UI, voice, and other project-relevant categories.
- Configure bus effects, ducking, reverb/send logic, volume ranges, and accessibility controls at the system level rather than normalizing every sound independently.
- Give complete games an in-game settings surface appropriate to their scope. At minimum, when both categories exist, expose independent Music and SFX volume/mute plus a clear global mute or Master control; add ambience, UI, and voice controls only when those categories materially benefit the player.
- Make audio settings readable and operable with every supported input method. Labels and current values must not rely on an icon alone; compact games may use stepped controls, while broader games may use sliders and mute toggles.
- Apply controls through the intended audio buses, use a perceptually sensible volume-to-decibel mapping with true silence at the minimum, and keep button/slider preview sounds bounded so adjusting settings does not become noisy.
- Use `AudioStreamPlayer`, `AudioStreamPlayer2D`, or `AudioStreamPlayer3D` according to the desired spatial relationship.
- Put reusable event audio inside the relevant object/effect scene or a focused audio component; avoid one global script containing every sound path.
- Vary pitch/volume/sample selection within controlled ranges when repetition is undesirable.
- Save every exposed volume and mute setting, restore it before the first normal audible state, and keep the displayed controls synchronized with the actual buses. Music-off must not silently disable SFX, and global mute must restore the user's previous per-category levels when unmuted.
- Make settings reachable from an appropriate menu and, when the game has a pause flow, from pause without discarding gameplay state. Pause, focus loss, scene changes, restart, and advertisements/platform overlays must not leave orphaned playback or resume the wrong state.
- For Web targets, test the real browser path: respect user-gesture audio unlock/autoplay restrictions, tab focus changes, latency, streaming behavior, and compressed quality.
- Keep editable/high-quality masters outside the runtime export when appropriate. Import only the formats and variants the shipped platforms need; stream long music/ambience and keep short latency-sensitive sounds suitable for prompt playback.

Verify on the actual output path and with representative simultaneous sounds. Check clipping, masking, abrupt loops, excessive latency, distance attenuation, scene transitions, pause behavior, and saved volume settings.

## Music and adaptive layers

- Assign each cue a gameplay function and intended duration/state before selecting it. Keep form, pulse, harmony, instrumentation, density, and energy aligned with the requested experience; do not add generic cinematic, lo-fi, or upbeat-casual music by genre reflex.
- Prefer a deliberately authored loop, cue, or compatible set over a long track with no usable game form. Inspect intro, loop body, transition/outro behavior, and musical re-entry after pause or scene change.
- Reject aimless phrase structure, abrupt style/timbre drift, malformed transients, accidental noise/voice-like artifacts, unresolved transitions, exhausting density, or a loop seam that exposes the edit. These defects are especially common in unreviewed generated music but can occur in any source.
- For adaptive music, author compatible stems/segments and explicit transition rules. Test bar/beat alignment, loop boundaries, and state changes.
- Separate composition rights, master/recording rights, and any sample-library obligations when relevant.
- Do not claim a generated or sourced track is shippable until its terms and actual file have been inspected.

Purposeful silence is better than an unrelated track, but it must be an intentional direction rather than an excuse for an unfinished full-game mix.

## Voice

- Store dialogue identity, locale, take/version, processing, and subtitle key consistently.
- Keep editable script/text separate from rendered voice files.
- Verify pronunciation, pacing, noise, clipping, emotional consistency, and synchronization in the real scene.
- Plan fallbacks for localization and accessibility; voice must not be the sole carrier of critical information unless the design explicitly requires it.

## Audio acceptance evidence

For a complete game or vertical slice, do not mark audio verified without all applicable evidence:

- the sonic direction and event map identify the intended system rather than only listing filenames;
- source/author/license or approved generation/edit provenance is present in the asset manifest;
- representative gameplay was listened to for several minutes with common overlaps and repeated actions, not merely opened in an audio editor;
- a capture or listening note covers core action, pressure, success/failure, UI, music/ambience, transitions, pause/focus, and volume settings as applicable;
- volume/mute controls were exercised with every supported input path and survived scene changes, reload/relaunch, focus loss, and platform overlays; the UI values matched the actual audible result;
- phone/laptop speakers or an equivalent narrow-band/mono check did not erase essential feedback, while headphones did not reveal clicks, harshness, bad spatialization, or obvious loop seams;
- the exported target was checked for startup unlock, latency, compression damage, missing streams, clipping/masking, and correct pause/resume behavior;
- remaining placeholders, unlicensed candidates, unreviewed cues, and unavailable-device checks are reported explicitly.

An independent listener or human playtest should score the audio. The building agent must not infer quality from filenames, waveform existence, node configuration, or its own implementation intent.

## VFX as reusable Godot scenes

Prefer native reusable effect scenes/resources when the effect benefits from interaction, parameterization, timing, or camera/world integration:

```text
HitEffect2D/3D
|-- Particle node(s)
|-- AnimationPlayer
|-- Light or decal when appropriate
|-- AudioStreamPlayer2D/3D
`-- Lifetime/controller script
```

- Use particles, shaders, curves, gradients, decals, trails, lights, animated materials, and sprites as a coherent effect system.
- Expose meaningful parameters such as color family, scale, direction, intensity, lifetime, and surface response.
- Keep effect timing readable at gameplay scale and under realistic overlap.
- Pool or reduce high-frequency effects when allocation/overdraw becomes material.
- Check transparency sorting, screen-reading shaders, particles, shadow/decal cost, and renderer/platform limitations.
- Use baked flipbooks/video only when they provide a deliberate visual/performance advantage; preserve source and import them consistently.

Effects should communicate cause and priority. Do not add bloom, sparks, shake, trails, or particles to every interaction by default.

## Fonts and typography

- Verify font license, redistribution/embedding terms, required attribution, supported scripts, weights/styles, and variable-font axes.
- Test the actual languages and characters the project supports; configure fallback fonts rather than accepting missing glyph boxes.
- Build typography through shared Godot `Theme`/font resources, type variations, sizes, spacing, outlines/shadows, and contrast rules.
- Keep hierarchy limited and intentional. Do not mix fonts merely to make the interface look “designed”.
- Test small text, dense UI, large headings, dynamic numbers, long localization strings, high DPI/UI scale, and supported renderers.
- Keep important text as text. Do not bake dynamic/localized copy into generated UI images.

## Verification

Inspect sound, effects, and typography together with gameplay—not as isolated previews. Record important files and obligations in the asset manifest, create reusable Godot resources/scenes, and mark them `verified` only after representative runtime inspection.
