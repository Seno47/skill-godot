# Asset Sourcing

Read this before searching for, comparing, downloading, purchasing, or licensing third-party assets. A search result or preview is not a usable asset until its exact source, rights, files, and technical fit are verified.

## Write an asset brief before searching

Derive a compact search brief from the game and art direction:

- gameplay role and required variants;
- 2D view/projection or 3D scale and camera distance;
- silhouette, palette, material/texture language, and detail density;
- dimensions, frame/grid needs, topology/rig/animation needs, texture maps, or audio duration/loop needs;
- target Godot version, renderer, platform, and performance budget;
- acceptable license, attribution, budget, account, and redistribution constraints;
- required editable/source format and preferred runtime format;
- explicit rejection criteria.

Do not search for a generic noun when perspective, style, format, or gameplay use materially affects the result. Search queries should combine the subject with the relevant constraints.

## Detect capabilities and authorization

- Use available web/search/catalog tools when the user's request includes asset sourcing.
- If the environment has no network or signed-in marketplace access, work from user-provided/local assets and say what could not be searched.
- Browsing and comparison do not authorize purchases, paid subscriptions, accepting new legal terms, publishing, or enabling third-party code.
- Download only candidates needed for inspection or integration. Avoid bulk-downloading a catalog.
- Never execute an installer or enable a Godot addon merely to preview its art.

## Search and shortlist

1. Search several targeted queries or relevant catalogs rather than accepting the first visually plausible result.
2. Open the exact asset/product page. Do not rely on a search-engine thumbnail, mirror, repost, aggregator summary, or preview CDN URL.
3. Confirm that downloadable files exist in useful formats and the displayed preview represents those files.
4. Build a shortlist of the strongest candidates. Record source page, author/publisher, price, license, attribution, formats, dependencies, update/version notes, and why each fits.
5. Compare candidates using the acceptance gate below.

Ask the user to choose when the decision costs money, requires an account/legal acceptance, or materially changes the game's artistic identity. When constraints clearly determine a free and compatible choice, select it and document why.

## Acceptance gate

Evaluate every candidate across five dimensions:

| Dimension | Questions |
| --- | --- |
| Artistic fit | Does silhouette, perspective, palette, material language, animation, and detail density match the established direction? |
| Gameplay fit | Is it readable at gameplay scale and does it provide the states, pivots, sockets, collision intent, or variants the mechanic needs? |
| Technical fit | Are format, resolution, topology, rig, texture maps, audio format, Godot version, renderer, and target platform suitable? |
| Rights fit | Is the asset-specific license visible and compatible with the intended distribution, modification, attribution, and source-sharing model? |
| Integration cost | How much cleanup, conversion, retopology, re-rigging, repainting, material work, or custom code is required? |

Reject a visually strong asset when rights are unclear or adaptation cost defeats the purpose of using it.

## Verify provenance and license

- Read the license attached to the exact asset/version, not only the site's general description.
- Record the canonical source URL, author/publisher, license name/version or marketplace license, license URL/file, attribution text, purchase/order evidence location when applicable, and date/version acquired.
- Distinguish public-domain/CC0, attribution licenses, copyleft/content-share-alike licenses, marketplace licenses, custom licenses, and assets with no grant.
- Check whether modification, commercial distribution, source redistribution, use in generated datasets, and inclusion in templates/asset packs are restricted when relevant.
- Treat “free”, “royalty-free”, and “downloadable” as price/marketing terms, not a license.
- If the license is missing, contradictory, or uncertain, keep the asset as a candidate only; do not ship it or provide legal certainty.

Record important assets with `scripts/asset_manifest.py`. Attribution obligations should also be transferred into the game's credits/release process; a private manifest alone is not fulfillment.

## Inspect archives and packs safely

- Download to a bounded temporary work area outside the Godot project when practical so rejected files are not imported.
- Preserve the original archive or canonical source file only when provenance, future editing, or license compliance benefits from it.
- Inspect archive paths before extraction; reject path traversal, unexpected executables, installers, symlinks, or unrelated payloads.
- Inspect scripts, native libraries, `@tool` scripts, editor plugins, autoloads, project settings, and dependencies before copying a Godot pack/addon into the project.
- Do not copy an entire demo project when only a small art subset is needed.
- Keep license and attribution files associated with the accepted asset.

## Ready-made pack strategy

Treat a pack as a library, not a visual direction. First test one hero object and one representative environment combination in the real project. Decide which subset belongs, then adapt it through [asset-integration.md](asset-integration.md).

Avoid mixing packs because they share a broad label such as “low-poly”, “pixel”, or “fantasy”. Compare actual proportions, camera assumptions, outlines, texture density, palette, lighting response, animation cadence, and UI language.

## Stop conditions

Stop searching and change approach when:

- repeated candidates fail the same hard requirement;
- only unclear or incompatible licenses are available;
- adaptation cost exceeds creating a targeted asset;
- the required marketplace/account cannot be accessed;
- the user must choose between materially different art directions or paid options.

At that point, propose generation, in-house creation, a scoped placeholder, or a revised brief rather than continuing an unbounded search.
