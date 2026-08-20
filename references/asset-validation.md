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
- Attribution or notice obligations have a path into credits/release artifacts.
- Unclear rights keep an asset at `candidate`; they do not become a claim of legal safety.

## Technical and integration gate

- Accepted source/runtime files exist at stable paths; rejected/demo/duplicate payloads were not copied unnecessarily.
- Godot import settings match the target renderer/platform/use.
- Scale, pivot, perspective, palette, texture density, materials, animation, audio, fonts, and variants fit the project.
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

At handoff, report origin/license status, adaptations, integration scene/resource, and any remaining attribution or replacement work.
