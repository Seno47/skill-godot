# Accounts, cloud saves, and cross-progression

Use this guide when local/guest progress can be linked, synchronized, restored, or shared across devices or platform identities. Also read the save-data guide.

## Identity and conflict contract

Record stable internal player ID, provider identities, guest ownership, link/unlink rules, account switching, cloud revision/vector or timestamp basis, deterministic merge boundaries, user-choice conflict UX, preserved backup, offline queue, deletion/export behavior, and token/log redaction. Instantiate `assets/account-cloud-contract.template.json`.

Do not equate the current OS/store user with the game profile without an explicit mapping. Do not silently overwrite meaningful guest progress with an empty/new cloud or merge currencies, purchases, inventory, quests, and achievements by one generic “largest value wins” rule. If deterministic merging is safe, prove it per data type and keep a rollback copy; otherwise show both versions and let the player choose.

## Required state matrix

Split acceptance into two explicit layers:

- Builder-owned `account_cloud_evidence` proves the production client adapter, resolver and durable state against project-owned provider doubles or injected responses: guest start, sign-in/link callbacks, empty/conflicting payloads, multi-device/offline inputs, switch/sign-out, outage/error responses and deletion requests. Each trace shows user isolation, stable identity, idempotent sync, exact expected digest, preserved fallback, no silent overwrite and no token/PII leakage.
- Provider-owned `account_cloud_provider_evidence` replays the required matrix through real provider accounts and the unchanged target candidate: actual guest/link, two-device/offline conflict, switch/sign-out, outage behavior and provider-confirmed deletion. A local SDK mock, deterministic resolver, production-shaped fixture or callback replay cannot pass this layer. If provider/account access is unavailable while the builder layer passes, leave this gate `NOT TESTED` as an external boundary; it permits `BUILDER_COMPLETE / READY_FOR_HUMAN_TEST` but not `PUBLICATION_CERTIFIED`.

An observed provider failure that exposes a client defect returns to the builder for repair. A provider-only unavailable operation remains external rather than being converted into a user checklist.

Run `scripts/account_cloud_probe.py`, then use `assets/account-cloud-review.template.md` for an independent conflict/account-switch UX review.

## Primary references

- [Google Play Games saved games](https://developer.android.com/games/pgs/savedgames)
- [Google Play Games conflict resolution](https://developer.android.com/games/pgs/android/saved-games)
- [Steam Cloud](https://partner.steamgames.com/doc/features/cloud?l=english)
- [Xbox game saves](https://learn.microsoft.com/en-us/gaming/gdk/docs/features/common/game-save/xgamesave?view=gdk-2604)
