# Asset Source Catalogue

Read this reference only when concrete third-party asset discovery is part of the task. It maps asset needs to useful canonical sources; it is not an allowlist and does not replace the candidate and license checks in [asset-sourcing.md](asset-sourcing.md).

Snapshot date: **2026-08-24**. Recheck the exact asset page and terms at acquisition time because catalogues, prices, accounts, files, and licenses change.

## Select a source route

Start from the missing production role, not from a favorite website:

| Need | Start here | Escalate when needed |
| --- | --- | --- |
| Godot addon, template, demo, import tool | [Godot Asset Library](https://godotengine.org/asset-library/asset) | Canonical upstream repository and release page; then [evaluated-ecosystem.md](evaluated-ecosystem.md) for reviewed options |
| Cohesive 2D pack, UI, input prompts, simple audio | [Kenney](https://kenney.nl/assets), [OpenGameArt](https://opengameart.org/), [itch.io game assets](https://itch.io/game-assets) | A commissioned or generated style-matched set when packs cannot provide the required perspective/states |
| Stylized low-poly 3D kit | [Quaternius](https://quaternius.com/), [KayKit](https://kaylousberg.com/game-assets), [Kenney](https://kenney.nl/assets) | A style-matched marketplace pack or custom modeling for hero assets |
| Realistic 3D environment, PBR material, HDRI | [Poly Haven](https://polyhaven.com/), [ambientCG](https://ambientcg.com/), then exact licensed models on [Sketchfab](https://sketchfab.com/features/free-3d-models) | Custom scan/model or a paid source with a verified production license |
| Humanoid auto-rig or animation starting point | [Adobe Mixamo](https://www.mixamo.com/) | Project-owned animation, mocap cleanup, or a specialist pack when the motion language is distinctive |
| Recorded SFX and ambience | [Freesound](https://freesound.org/), [Sonniss GameAudioGDC](https://sonniss.com/gameaudiogdc/), [OpenGameArt](https://opengameart.org/), [Kenney](https://kenney.nl/assets) | Custom foley/field recording or a paid library when identity, coverage, or consistency is missing |
| Music | [OpenGameArt](https://opengameart.org/), [itch.io game assets](https://itch.io/game-assets), composer storefronts | Commission or license a coherent soundtrack; do not assemble unrelated tracks merely because each is individually usable |
| UI/gameplay icons | [Kenney](https://kenney.nl/assets), [Game-icons.net](https://game-icons.net/) | A project-owned icon family when generic symbols do not match the game's shapes and stroke language |
| Fonts | [Google Fonts](https://fonts.google.com/) | A paid family or custom lettering when brand identity requires it |
| Godot shader or VFX technique | [Godot Shaders](https://godotshaders.com/), [Godot Asset Library](https://godotengine.org/asset-library/asset) | Project-authored shader after renderer and performance constraints are known |

Search only the routes relevant to the brief. Do not load a project with assets from every row.

## Source notes and license posture

The posture below describes the catalogue, not a grant for an arbitrary download.

| Source | Best for | Rights/account posture | Production cautions |
| --- | --- | --- | --- |
| [Godot Asset Library](https://godotengine.org/asset-library/asset) | Godot-native plugins, scripts, tools, demos, templates, materials | Mixed licenses per entry; filter by Godot version, category, support level, and license. Browsing/installing does not prove upstream compatibility. | Open the canonical upstream, pin a release, and audit code, autoloads, settings, dependencies, removal, and export targets before adoption. `Testing` support is not a production endorsement. |
| [Kenney](https://kenney.nl/assets) | Cohesive 2D, 3D, UI, input prompts, audio, pixel art, and textures | Kenney states that assets on its asset pages are CC0 and usable commercially without attribution; retain the included license/source record anyway. | Packs are common and recognizable. Re-art-direct palette, materials, UI composition, and hero assets so the result is not a stock-pack collage. Do not reuse the Kenney logo as project identity. |
| [OpenGameArt](https://opengameart.org/) | 2D, 3D, textures, concept art, music, and SFX | User-uploaded and mixed per-item licenses including CC0, attribution, share-alike, and GPL-family options. Commercial use depends on the exact item and compliance. | Record author, exact asset URL, selected license among alternatives, attribution, DRM/store implications, and derivative obligations. Do not rely on a search preview or site-wide assumption. |
| [itch.io game assets](https://itch.io/game-assets) | Free and paid packs across 2D, 3D, UI, audio, fonts, tools | Marketplace/platform: the publisher controls the asset grant, tiers, price, and download terms. “Free” or “name your own price” is not a license. Account/checkout may be required. | Save the exact product page, tier, version, included license/EULA, receipt when paid, and redistribution restrictions. Check that preview content belongs to the purchased/downloaded tier. |
| [Poly Haven](https://polyhaven.com/) | Human-made photoreal HDRIs, PBR textures, and 3D models | Poly Haven publishes its downloadable assets under CC0 with no account or attribution required; website branding/previews and API terms are separate. | Assets can be much heavier than an indie/mobile budget. Select resolution deliberately, convert to Godot-friendly maps/formats, create LODs/collisions as needed, and profile VRAM. |
| [ambientCG](https://ambientcg.com/) | CC0 PBR materials, decals, HDRIs, and some models | The downloadable asset files are published under CC0; preserve the canonical asset page and acquisition date. | Choose only required maps/resolutions. Verify normal-map convention, channel packing, tiling scale, color space, and compressed import settings rather than importing every supplied file. |
| [Quaternius](https://quaternius.com/) | Coherent stylized low-poly characters, props, environments, and animations | Quaternius states its models are CC0 and usable commercially without attribution. Downloads commonly include editable/interchange formats. | Test atlas/material ownership, scale, pivots, animation naming, skeleton compatibility, collision, silhouette at gameplay distance, and actual draw-call/material count. |
| [KayKit](https://kaylousberg.com/game-assets) | Stylized low-poly themed kits, characters, animation, environment sets | Many individual packs state CC0 and offer free/paid content tiers through itch.io, but verify the exact pack and tier rather than inferring one rule for the whole storefront. | Prefer GLTF when supplied. Confirm which models, recolors, source files, and animations belong to the acquired tier; do not assume bundle previews are in the free archive. |
| [Sketchfab](https://sketchfab.com/features/free-3d-models) | Individual 3D models, scans, cultural objects, niche props | Mixed Creative Commons, paid standard, and editorial licenses; downloads require exact per-model review and often an account. Attribution follows CC models. Editorial assets are not ordinary commercial game assets. | Check authorship plausibility, trademarks/people, derivative restrictions, topology, rig, textures, scale, and standalone-redistribution limits. A downloadable preview does not establish clean rights. |
| [Adobe Mixamo](https://www.mixamo.com/) | Biped humanoid auto-rigging and animation starting points | Adobe says characters and animations can be used royalty-free in commercial games; an Adobe ID is required and service restrictions apply. | It is for biped humanoids, not a final motion direction. Retarget carefully, repair root motion/loops/contacts, keep local source copies, and validate the current Adobe terms before release. |
| [Freesound](https://freesound.org/) | Specific field recordings, foley, ambience, machinery, impacts, and unusual source sounds | User-uploaded; current choices include CC0, CC BY, and CC BY-NC. Some assets cannot be used commercially and many require attribution. Account/download rules may apply. | Prefer credible recordings with useful metadata. Inspect waveforms and listen for noise, clipping, baked reverb, speech, music, trademarks, duplicates, and implausible provenance. Keep each sound's author, ID, URL, license, and attribution. |
| [Sonniss GameAudioGDC](https://sonniss.com/gameaudiogdc/) | Large professional SFX source library for game/film sound design | Custom GameAudioGDC EULA: royalty-free commercial media use and modification, no required attribution, but no standalone redistribution; AI/ML training is prohibited. | Accept and archive the applicable license; the bundles are huge, so search and extract only selected sources. Layer/edit/master them into a coherent event map instead of dropping raw files into the build. |
| [Game-icons.net](https://game-icons.net/) | Searchable monochrome SVG gameplay and UI symbols | Most of the collection is CC BY 3.0 and requires author credit; some individual icons may be public domain. | Record the author of every chosen icon. Normalize stroke, fill, optical size, corner language, and semantic meaning; cherry-pick does not automatically create a coherent project icon family. |
| [Google Fonts](https://fonts.google.com/) | Open-source display and text fonts with script filtering | Google states the catalogue uses open-source licenses and allows commercial use. Each font family still has its own license file. No web API is needed to bundle a local font in Godot. | Download and ship local TTF/OTF files, record the family license, verify Cyrillic/Latin and required glyphs, test hinting/readability, and subset only through a reproducible font workflow. |
| [Godot Shaders](https://godotshaders.com/) | Godot-specific canvas, spatial, post-process, and VFX shader examples | License is selected per post (for example CC0, MIT, or GPLv3). The site's license applies to shader/code snippets, not automatically to preview images, videos, or depicted assets. | Confirm Godot 4 syntax, renderer, depth/normal assumptions, clipping, alpha, mobile compatibility, and measured GPU/overdraw cost. Adapt the visual language instead of treating a popular effect as art direction. |

## Search query recipes

Add only constraints that affect selection:

```text
[gameplay subject] + [view/projection] + [style] + [required states] + [format]
[prop/environment] + [realistic or stylized] + glTF/GLB + PBR/atlas + [poly budget]
[character] + [rig type] + [animation list] + glTF + [license requirement]
[sound event] + field recording/foley + dry + variations + [duration]
[music role] + [mood] + loop + stems + [duration] + [license requirement]
[font role] + Cyrillic Latin + [tone] + open-source license
[Godot 4 shader role] + canvas_item/spatial + [renderer] + mobile
```

For 2D, include the actual camera assumption: top-down, side view, isometric/dimetric, front-facing portrait, eight-direction, tile size, frame count, and pivot needs. For 3D, include real-world scale, skeleton/rig, animation, material workflow, texture budget, LOD, and target runtime format. Search terms such as “beautiful”, “game-ready”, or “free” do not replace these constraints.

## Shortlist and stopping rule

1. Search two or three relevant canonical routes, not every catalogue.
2. Keep at most three to five serious candidates per role after hard rejections.
3. Add candidates to the project asset manifest with `scripts/asset_manifest.py`; put price/tier, formats, account requirement, style-fit notes, and rejection reasons in `notes` until accepted.
4. Compare the candidates in the actual camera/UI scale. For packs, test one hero object plus one representative environment/UI combination before bulk integration.
5. Stop when one candidate clears artistic, gameplay, technical, rights, and integration-cost gates. More browsing after that needs a concrete unresolved requirement.

If no candidate clears the gate, change the plan: commission, generate, author, record, or deliberately combine a narrow base pack with project-owned hero work. Never lower the rights gate to end a search.

## Example source stacks, not default art directions

- **Stylized low-poly 3D:** one primary Quaternius, KayKit, or Kenney world family; project-owned hero silhouettes/material variants; Kenney or authored input prompts; selected human-recorded Freesound/Sonniss sources; a Google Fonts family with verified language coverage.
- **Realistic 3D:** Poly Haven HDRI/materials plus ambientCG gaps; only a few exact licensed Sketchfab/custom models; authored collision/LOD/material wrappers; recorded source audio; local licensed fonts.
- **Cohesive 2D:** one Kenney/OpenGameArt/itch.io pack family chosen for the exact projection and frame needs; authored palette/outline cleanup and hero sprites; one normalized icon family; recorded SFX and a separately licensed coherent music direction.
- **UI-heavy casual game:** a custom scene-authored Godot theme built from a restrained Kenney or project-owned nine-slice/icon base; typography selected for every shipping language; non-generic sound palette made from recorded layers and variations.

These stacks are discovery examples only. The game brief decides whether a source belongs. A source stack passes only when the result looks intentionally art-directed in representative gameplay captures rather than like recognizable packs placed side by side.
