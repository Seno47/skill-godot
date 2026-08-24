<p align="center">
  <img src="./assets/readme/hero.svg" width="100%" alt="skill-godot turns a game brief into a verified, editable Godot 4 project">
</p>

<p align="center">
  <strong>A production-focused Codex skill for building and polishing Godot 4 games.</strong><br>
  <a href="./README.ru.md">Русская версия</a> · <a href="https://learn.chatgpt.com/docs/build-skills">How Codex skills work</a>
</p>

`skill-godot` gives Codex a repeatable workflow for creating real Godot projects: authored scenes and resources, coherent assets, playable controls, deterministic checks, visual review, performance evidence, and release-ready exports. It covers 2D, 3D, 2.5D, isometric and orthographic games, UI, audio, mobile/web input, and Yandex Games releases.

## Quick start

Ask Codex to install this repository:

```text
Use $skill-installer to install https://github.com/Seno47/skill-godot
```

Then start a game task explicitly:

```text
Use $skill-godot to build a polished isometric café game in Godot 4.
Keep the world editable in scenes and resources, support mouse and touch,
then run the game and verify the core loop at desktop and mobile sizes.
```

Codex can also select the skill automatically when a request clearly matches its description.

## What makes it useful

| Included | What it gives you |
| --- | --- |
| 28 focused production guides | Scene architecture, 2D/3D/2.5D, UI, genre systems, asset-source discovery, art, audio, performance, loading, exports, and platform release work |
| 16 deterministic Python helpers | Project snapshots, scene/asset audits, screenshot parity, fixed-camera readability, progression/economy probes, capture support, budgets, scorecards, and build-size checks |
| 7 reusable Godot probes | Touch scrolling, button composition, third-person controls/HUD mouse routing/visibility, isometric projection, and isometric navigation checks |
| Scene-first authoring rules | Persistent composition stays in `.tscn` scenes and Godot resources instead of disappearing into large runtime scripts |
| Evidence-based completion | The skill runs the project, checks representative viewports, and avoids claiming polish or optimization without proof |

## The production loop

```mermaid
flowchart LR
    A[Game brief] --> B[Inspect the project]
    B --> C[Build editable scenes and resources]
    C --> D[Play and capture representative flows]
    D --> E[Audit visuals, behavior, performance and exports]
    E --> F[Verified playable result]
    E -. findings .-> C
```

The main [`SKILL.md`](./SKILL.md) is a compact router. It sends Codex only to the references, templates, components, and tests relevant to the current game task.

## Coverage

- **Game production:** gameplay, levels, camera, lighting, collision, navigation, UI, onboarding, audio, VFX, and asset integration.
- **2D and 3D:** native Godot scene patterns with focused guidance for each dimension.
- **2.5D and isometric:** explicit spatial contracts for projection, picking, sorting, elevation, occlusion, pathfinding, and hybrid 2D/3D presentation.
- **Input:** keyboard, mouse, controller, camera-relative locomotion, orbit/capture recovery, touch, drag gestures, and mobile viewport checks.
- **Optimization:** measured FPS, CPU/GPU/physics investigation, memory and loading analysis, and export-size budgets.
- **Web and Yandex Games:** SDK lifecycle, advertisements, rewarded flows, saves, leaderboards, localization, moderation, and archive QA.
- **Validation:** headless checks, deterministic probes, automated captures, interactive onboarding verification, and independent UX review.

The genre layer now adds conditional production contracts for fighting games, metroidvanias, idle/clicker economies, and quest systems without turning their community examples into universal architecture. A reviewed ecosystem catalogue records when menu/settings frameworks, UI themes, portal bridges, combat addons, shaders, and component libraries are useful, experimental, obsolete, license-restricted, or likely to conflict with an existing project's ownership.

Asset discovery has its own source router for 2D, 3D, UI, recorded audio, music, fonts, shaders, and animation. It distinguishes broad CC0 libraries from mixed-license community catalogues and custom marketplace EULAs, then requires exact-item provenance, a bounded shortlist, style-fit review, and Godot integration checks before an asset is accepted.

Approved UI references get a native parity workflow: formal screens remain editor-visible scenes, while [`image_compare.py`](./scripts/image_compare.py) creates same-resolution side-by-side, overlay, and diff artifacts. Progression topology and idle curves have reusable JSON models and deterministic probes; their numerical PASS still requires target-build play and human UX review.

## Isometric and 2.5D workflow

The skill does not treat “isometric” as an art style alone. It establishes one testable spatial contract before gameplay code spreads across the project:

1. Choose the primary architecture: `Node2D`, `Node3D`, or a deliberate hybrid.
2. Define grid axes, tile ratio, origin, elevation step, sort key, picking rule, and navigation representation.
3. Store the contract using [`isometric-spatial-contract.template.md`](./assets/isometric-spatial-contract.template.md).
4. Reuse [`isometric_projection.gd`](./assets/godot-components/isometric_projection.gd) where its contract fits.
5. Adapt the projection and navigation probes to catch round-trip, height-transition, and route regressions.
6. Before bulk level authoring, pass the gameplay-size hero/mechanism/objective/decor/lighting/UI gate in [`isometric-complete-review.template.md`](./assets/isometric-complete-review.template.md).
7. Measure same-frame hero/background separation with [`isometric_readability_audit.py`](./scripts/isometric_readability_audit.py), review route/density composition independently, and support release-duration claims with [`content-duration-contract.template.md`](./assets/content-duration-contract.template.md).

The full decision guide lives in [`references/isometric-and-2-5d.md`](./references/isometric-and-2-5d.md).

## Third-person 3D verification

For a freely orbiting camera, the skill verifies camera-relative movement after yaw, real mouse motion through the visible production HUD, right-stick X/Y, zoom/recenter, camera collision restoration, player visibility through multiple occluders and real openings, exact high-structure route contrast, cutaway restoration, pause/focus capture recovery, HUD/world sightlines, pressure-safe onboarding, and human audio listening. Adapt [`third_person_controller_probe.gd`](./assets/godot-tests/third_person_controller_probe.gd), [`third_person_hud_mouse_probe.gd`](./assets/godot-tests/third_person_hud_mouse_probe.gd), and [`third_person_visibility_probe.gd`](./assets/godot-tests/third_person_visibility_probe.gd), then complete [`third-person-3d-review.template.md`](./assets/third-person-3d-review.template.md); code inspection, direct look-method calls, or SpringArm success alone cannot pass these gates.

Complete games also use [`semantic-identity-review.template.md`](./assets/semantic-identity-review.template.md): the exported app icon and main-menu mark must communicate a game-specific idea at their real display sizes in a blind independent review. A coordinated palette or tidy primitive geometry alone is not semantic identity.

## Installation options

The `$skill-installer` prompt above is the simplest option. For a manual user-scoped installation, clone the repository into the current Codex user skill location.

Windows PowerShell:

```powershell
git clone https://github.com/Seno47/skill-godot "$env:USERPROFILE\.agents\skills\skill-godot"
```

macOS or Linux:

```bash
git clone https://github.com/Seno47/skill-godot "$HOME/.agents/skills/skill-godot"
```

For a skill shared only inside one project, clone or vendor it under `.agents/skills/skill-godot` in that repository. Codex detects skill changes automatically; restart Codex if a newly installed skill does not appear. See the [official OpenAI skill documentation](https://learn.chatgpt.com/docs/build-skills) for discovery scopes and invocation details.

To update a manual installation:

```bash
git -C "$HOME/.agents/skills/skill-godot" pull --ff-only
```

## Example prompts

```text
Use $skill-godot to turn this prototype into a maintainable vertical slice.
Preserve the existing art direction, add touch controls, and verify onboarding.
```

```text
Use $skill-godot to diagnose frame-time spikes in this Godot 4 project.
Measure first, identify the bottleneck, apply a focused fix, and compare evidence.
```

```text
Use $skill-godot to prepare this HTML5 game for Yandex Games.
Add the SDK lifecycle, saves, rewarded ads, leaderboards, Russian localization,
and run the release archive checks without changing the core game loop.
```

## Repository map

```text
skill-godot/
├── SKILL.md                 # Trigger scope and production workflow
├── agents/openai.yaml       # Codex UI metadata and default prompt
├── references/              # Focused production and release guidance
├── scripts/                 # Deterministic auditors and evidence helpers
├── assets/
│   ├── godot-components/    # Reusable Godot building blocks
│   ├── godot-tests/         # Adaptable deterministic probes
│   └── *.template.*         # Spatial, UX, capture, and release templates
├── evals/                   # Evidence schema and scoring rubric
└── tests/                   # Dependency-light and engine-backed tests
```

## Validate a checkout

Most tests require only Python 3:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

`scripts/image_compare.py` additionally uses Pillow; its tests skip cleanly when Pillow is unavailable, and the helper reports the missing dependency instead of weakening a parity claim.

The isometric smoke tests run against Godot 4 when `godot4`/`godot` is on `PATH`, or when `GODOT_BIN` points to the editor executable.

PowerShell example:

```powershell
$env:GODOT_BIN = "C:\Tools\Godot\Godot.exe"
python -m unittest discover -s tests -p "test_*.py"
```

## Contributing

Issues and focused pull requests are welcome. Please keep the skill scene-first, evidence-driven, Godot 4-specific, and progressively disclosed: add detailed material to a focused reference or reusable script instead of turning `SKILL.md` into a monolith. Run the test suite before opening a pull request.

## License and status

No license has been selected yet. Public availability does not grant a general reuse or redistribution license. This is an independent community project and is not an official Godot Engine or OpenAI project.
