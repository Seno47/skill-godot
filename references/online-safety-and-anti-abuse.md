# Online safety, anti-abuse, and moderation

Use this guide for competitive authority, anti-cheat/integrity, player reports, chat/UGC moderation, mute/block, sanctions, appeals, or privacy operations. It complements multiplayer, online-service, and modding guidance.

## Threat and operations contract

Record server-authoritative surfaces, hostile requests and rate limits, integrity signals, evidence minimization/retention, report abuse controls, mute/block semantics, sanction scope/expiry, review/appeal path, outage policy, audit ownership, and privacy deletion. Instantiate `assets/online-safety-contract.template.json`.

The client may provide evidence but must not decide durable sanctions or authoritative gameplay outcomes. Treat device/app integrity as one risk signal, not a sole automatic-ban oracle. Use proportional responses—retry, feature restriction, matchmaking separation, human review, or sanction—based on confidence and harm. Make false positives reversible and user messaging specific enough to explain the state without revealing detection internals.

## Required state matrix

Prove rejection of hostile gameplay requests, suspicious integrity signals, a false-positive review, authenticated/rate-limited report submission, immediate persistent mute/block, idempotent sanction enforcement, expiry/appeal restoration, moderation-service outage, and privacy deletion. Include abuse of the reporting path and cross-user authorization checks. Real operational staffing, escalation times, jurisdictional rules, and platform programs must be confirmed by the owner; do not invent them.

Run `scripts/online_safety_probe.py`, then complete `assets/online-safety-review.template.md` with an independent security/operations reviewer.

## Primary references

- [Google Play Integrity overview](https://developer.android.com/google/play/integrity/overview)
- [Steam anti-cheat and game bans](https://partner.steamgames.com/doc/features/anticheat)
- [Steam community moderation](https://partner.steamgames.com/doc/marketing/community_moderation?l=en)
