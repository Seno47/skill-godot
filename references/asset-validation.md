# Asset Validation

Read this only when external or generated assets are added, adapted, replaced, or prepared for release.

## Run deterministic checks

When the project uses an asset manifest:

```bash
python <skill-dir>/scripts/asset_manifest.py validate \
  --manifest <manifest.json> --project <project-dir>
python <skill-dir>/scripts/asset_audit.py \
  --project <project-dir> --manifest <manifest.json>
```

Use `--require-manifest` only when complete coverage is an explicit project convention. Use compact output while iterating and save machine-readable reports when many files are involved. A tiny project need not gain a manifest without practical provenance/maintenance value.

## Provenance and rights gate

- The canonical source/tool, author/publisher, asset-specific license/terms, version/date, and required attribution are recorded.
- Paid/account/legal acceptance was authorized and completed by the appropriate user.
- “Free” or “royalty-free” was not treated as a license.
- Generated assets record the actual generation/edit tool and relevant source context.
- Paid generation/acquisition has explicit user authorization, actual cost, and a bounded scope; a timeout was resumed from its recorded provider task/sidecar rather than silently charged twice.
- Attribution or notice obligations have a path into credits/release artifacts.
- Unclear rights keep an asset at `candidate`; they do not become a claim of legal safety.

## Technical and integration gate

- Accepted source/runtime files exist at stable paths; rejected/demo/duplicate payloads were not copied unnecessarily.
- Runtime-loaded asset directories are not hidden behind an accidental `.gdignore`; generation references, provider sidecars, rejected outputs, and QA previews live outside runtime import paths when the game does not load them.
- Godot import settings match the target renderer/platform/use.
- Scale, pivot, perspective, palette, texture density, materials, animation, audio, fonts, and variants fit the project.
- Visual assets record and pass their final gameplay-size/use contract (world meters, display pixels, tiling scale, crop behavior, or equivalent), not just source dimensions.
- Transparent assets have been inspected as composites over contrasting and representative game backgrounds; a raw alpha channel or checkerboard-looking source is not sufficient.
- Placeable/interactive concepts use wrapper or inherited scenes where useful.
- Collision, navigation, sockets, materials, effects, audio, and animation events were checked as applicable.
- Reimport preserves project-specific adaptations.
- Duplicate and oversized files are intentional or resolved.

## Status gate

Use the lifecycle honestly:

```text
candidate -> accepted -> adapted -> integrated -> verified
```

`accepted` requires artistic/technical/rights fit. `integrated` requires configured Godot resources/scenes. `verified` requires representative in-game visual/behavior inspection through [visual-validation.md](visual-validation.md) when presentation is involved.

At handoff, report origin/license status, adaptations, gameplay-size/use, authorized/actual external cost, resumable job record where relevant, integration scene/resource, and any remaining attribution or replacement work.
