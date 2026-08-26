# Localization and Globalization

Read this when the brief promises more than one locale, localized voice/assets, user-entered international text, or a global storefront release.

## Contract before copy multiplies

Record supported locales and scripts, fallback locale, source format, stable keys/contexts, plural and number/date policy, font and glyph coverage, BiDi/mirroring behavior, localized asset/voice variants, subtitle/caption limits, language persistence, and whether locale can change at runtime. Never encode English grammar as `count == 1`; use Godot plural translation APIs and test representative values for every locale family.

Keep gameplay identifiers separate from displayed text. Formatting, sorting, search, case conversion and input validation must not assume ASCII. User-entered names/chat need the declared TextServer/IME path, length policy in graphemes rather than bytes where applicable, and safe fallback for unsupported glyphs.

## Target-build matrix

Exercise the shortest locale, the longest real locale, pseudolocalization, a non-Latin script, and RTL/CJK where promised. Cover menu, settings, onboarding, dense HUD, level/content cards, dialogue/subtitles, numbers, save/load and result states at narrow and wide target viewports. Verify live locale switch invalidates cached text/layout, directional icons mirror only when semantics require it, voice/subtitle assets stay paired, and missing keys are visible failures rather than shipping key strings.

Use `assets/localization-contract.template.json`, run `scripts/localization_probe.py`, and complete `assets/localization-review.template.md`. A translation table with no overflow/glyph/plural evidence does not pass.

Primary Godot references:

- [Internationalizing games](https://docs.godotengine.org/en/stable/tutorials/i18n/internationalizing_games.html)
- [Pseudolocalization](https://docs.godotengine.org/en/4.7/tutorials/i18n/pseudolocalization.html)
