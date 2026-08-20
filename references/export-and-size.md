# Export and Size Optimization

Read this only for release exports, package/download/install size, web transfer size, patch/DLC size, or size regressions. “Game weight” is not one metric.

## Define the size contract

Track separately per platform/preset:

- repository/source-art size;
- project resource/import-cache size;
- exported executable/app/package and PCK size;
- compressed download/archive size;
- installed size;
- patch/update size;
- RAM/VRAM at runtime.

Record Godot version, export preset, architecture, renderer, build type, compression/embedding choices, and whether symbols/templates are included. Compare like with like.

## Measure before removing

Use `scripts/build_size_audit.py` to inventory export outputs, list largest files/categories, compare a baseline report, and enforce preset budgets. Use `asset_audit.py` for source/project assets.

Run one named profile per comparable export preset. The JSON report can be reused as the next baseline:

```bash
python scripts/build_size_audit.py --artifact windows-release=build/windows --budget-mb windows-release=500 --baseline previous-size.json --summary --json-output current-size.json
```

Do not delete source assets or production files merely because an export is large. First determine whether they are actually included and why.

## Control exported resources

- Review each export preset's resource mode: all resources, selected scenes/resources with dependencies, exclusions, or dedicated server.
- Prefer dependency-based selected scenes/resources when the project's dynamic loading model is compatible and coverage is tested.
- Include dynamically addressed non-resource/data files explicitly; static dependency discovery cannot infer arbitrary runtime strings/mod content.
- Exclude demos, source-working files, unused variants, development captures, attribution duplicates, and platform-irrelevant payloads from the export without breaking the source repository.
- Keep required license/notice/credits files even when minimizing.
- Validate every reachable scene, dynamic load, locale, quality tier, and platform after filters change.

Files/folders beginning with a period are not exported by Godot, but do not rely on hidden folders for required runtime content.

## Optimize content by runtime need

- Configure platform-appropriate texture compression, dimensions, mipmaps, channels, and quality. Source PNG/JPG size is not imported texture/VRAM size.
- Stream long music/ambience and choose appropriate compression; keep short latency-sensitive samples suitable for memory playback.
- Remove unneeded animation tracks/clips, model variants, material/texture duplicates, oversized lightmaps, and unused language/font data when evidence supports it.
- Reuse shared runtime resources; verify that atlases/bundles do not force unnecessary residency or patch churn.
- Keep editable source formats outside export selection while retaining them in version control when useful.

## Engine and packaging tradeoffs

- Use release export templates for shipped builds.
- PCK is the normal fast-seeking pack; ZIP can be smaller/slower and has different launch/modding behavior. Compare actual download and startup requirements.
- Shader baking in supported newer renderers can increase PCK size by megabytes while reducing initial shader work; decide from startup and size budgets together.
- For web, configure server-side Brotli/gzip and cache headers for actual transfer-size improvements.
- Custom feature-disabled export templates can greatly reduce engine binary size but increase build, QA, maintenance, and platform complexity. Use only when ordinary resource/import/export optimization cannot meet a real budget.
- Symbols aid crash diagnosis; stripping them is a release/debuggability tradeoff, not an automatic cleanup.

## Validation gate

Export the actual target preset and run it on the target platform. Verify cold start, all reachable/dynamically loaded content, locales, saves, network/mod/DLC paths if applicable, and visual/audio quality after compression.

Record total artifact size, compressed transfer/install size where relevant, top contributors, baseline delta, budget result, export command/preset/version, and intentional tradeoffs. A smaller build that cannot load content or diagnose crashes is a regression.

For a Yandex Games target, also read [yandex-games-web.md](yandex-games-web.md); its archive root, SDK loader, local-mock exclusion, lifecycle, and debug-panel checks are platform gates rather than generic Godot size advice.

Official references:

- [Exporting projects and resource modes](https://docs.godotengine.org/en/stable/tutorials/export/exporting_projects.html)
- [Optimizing a custom build for size](https://docs.godotengine.org/en/stable/engine_details/development/compiling/optimizing_for_size.html)
- [Packs, patches, and mods](https://docs.godotengine.org/en/stable/tutorials/export/exporting_pcks.html)
