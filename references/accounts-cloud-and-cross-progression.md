# Accounts, cloud saves, and cross-progression

Use this guide when local/guest progress can be linked, synchronized, restored, or shared across devices or platform identities. Also read the save-data guide.

## Identity and conflict contract

Record stable internal player ID, provider identities, guest ownership, link/unlink rules, account switching, cloud revision/vector or timestamp basis, deterministic merge boundaries, user-choice conflict UX, preserved backup, offline queue, deletion/export behavior, and token/log redaction. Instantiate `assets/account-cloud-contract.template.json`.

Do not equate the current OS/store user with the game profile without an explicit mapping. Do not silently overwrite meaningful guest progress with an empty/new cloud or merge currencies, purchases, inventory, quests, and achievements by one generic “largest value wins” rule. If deterministic merging is safe, prove it per data type and keep a rollback copy; otherwise show both versions and let the player choose.

## Required state matrix

Prove guest start, new sign-in, linking to empty cloud, guest/cloud conflict, multi-device conflict, offline edits and reconnect, user switch, sign-out, provider outage, and account deletion. Each trace must show isolation between users, stable identity, idempotent sync, exact expected digest, no silent overwrite, and no token/PII leakage. Test the real provider path where release claims depend on it; a local mock only validates client behavior.

Run `scripts/account_cloud_probe.py`, then use `assets/account-cloud-review.template.md` for an independent conflict/account-switch UX review.

## Primary references

- [Google Play Games saved games](https://developer.android.com/games/pgs/savedgames)
- [Google Play Games conflict resolution](https://developer.android.com/games/pgs/android/saved-games)
- [Steam Cloud](https://partner.steamgames.com/doc/features/cloud?l=english)
- [Xbox game saves](https://learn.microsoft.com/en-us/gaming/gdk/docs/features/common/game-save/xgamesave?view=gdk-2604)
