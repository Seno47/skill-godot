# Modding and User-Generated Content

Read this when players can load mods, custom levels, texture/audio/model packs, scripts, Workshop items, shared blueprints, maps, or other UGC. Treat the format and trust boundary as a product API, not an unrestricted extension of `res://`.

## Choose the trust tier

Record one or more explicit tiers:

- **data-only:** validated JSON/custom schema selecting allowlisted IDs and numeric/text values;
- **media:** bounded runtime-loaded images/audio/models/fonts with decoded-size/type limits;
- **authored pack:** Godot PCK/ZIP resources following a documented namespace/API;
- **executable code:** scripts/native modules with full code-execution risk and a deliberately supported trust/distribution model.

Prefer the least powerful tier that serves the design. Do not present Godot Resource loading, PCK loading, GDScript, C# assemblies, GDExtension/native libraries, shell commands or downloaded executables as sandboxed. If arbitrary code is supported, say that it has the user's privileges and require explicit opt-in/trusted-source policy; a generic skill cannot manufacture a secure in-engine sandbox.

## Version and isolate content

Define manifest/schema version, mod ID/version/author/license, game/API compatibility, dependencies/conflicts/load order, hashes/signatures when used, namespace/path policy, allowed file types, compressed/uncompressed size and count limits, localization/content-rating fields, save dependencies and uninstall fallback.

Godot resource packs can override existing paths depending on `load_resource_pack()` options and order. Isolate community content under a dedicated namespace, reject traversal/absolute paths and collisions with protected game paths, and load early only when the architecture requires it. Runtime media import still needs bounded decode, dimensions/duration/polycount and failure placeholders.

Use `assets/modding-ugc-review.template.md` and test valid, malformed, oversized, traversal, collision, missing dependency, cycle, incompatible version, duplicate ID, corrupt archive/media, removed-mod save and safe-mode/no-mod startup. Confirm rejected content cannot partially mutate registries or saves, diagnostics identify the offending item without leaking private paths, and disabling one mod does not silently delete unrelated progress.

Workshop/store upload and moderation are external flows: record ownership/rights, visibility, update, report/takedown, age/privacy, download failure and offline behavior. Never auto-execute unknown payloads after download.

Primary Godot references:

- [Runtime file loading and saving](https://docs.godotengine.org/en/stable/tutorials/io/runtime_file_loading_and_saving.html)
- [Exporting packs, patches, and mods](https://docs.godotengine.org/en/stable/tutorials/export/exporting_pcks.html)

