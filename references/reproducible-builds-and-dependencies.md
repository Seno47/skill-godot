# Reproducible Builds and Dependencies

Read this for CI/CD, team handoff, release branches, multiple build machines, native addons, signed candidates, or claims that a release can be recreated.

Pin the exact Godot build/channel, export-template digest, renderer and project feature tags, language/runtime/toolchain versions, addon/plugin commits and native binaries, import-affecting tools, platform SDK versions, and export preset names. Commit `export_presets.cfg`; keep credentials, signing keys and upload tokens outside the repository and evidence.

A reproducible contract distinguishes source identity, toolchain identity, clean import, generated inputs, candidate packaging and signing. Compare normalized contents when platform containers embed unavoidable timestamps/signatures; never claim byte-for-byte reproducibility when only functional equivalence was measured. Produce an asset/license/dependency manifest with owner, source, version, license/EULA, platform and update policy.

CI must start from a clean checkout/cache policy, import with the intended editor, run tests, export exact named presets with the editor binary and installed templates, retain logs, and smoke the candidate. An export created only from a developer's warmed `.godot` cache is not reproducible evidence.

Use `assets/reproducible-build-contract.template.json`, run `scripts/reproducible_build_probe.py`, and complete `assets/reproducible-build-review.template.md`.

Primary Godot references:

- [Exporting projects](https://docs.godotengine.org/en/stable/tutorials/export/exporting_projects.html)
- [Command line tutorial](https://docs.godotengine.org/en/stable/tutorials/editor/command_line_tutorial.html)
