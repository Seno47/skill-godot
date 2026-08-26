# Commerce and entitlements

Use this guide for in-app purchases, paid currency, DLC, subscriptions, restores, or ownership-dependent content. Store UI is not the durable ledger.

## Contract before implementation

Record stable product IDs and types, supported stores, verification authority, account binding, grant ledger, idempotency key, acknowledge/consume policy, pending/offline UX, restore behavior, refund/revocation behavior, and test accounts. Instantiate `assets/commerce-entitlement-contract.template.json`.

Verify purchase authenticity before granting durable value. For valuable online currency or server-owned inventory, use an authoritative backend and make the transaction token/order ID an exactly-once ledger key. Never embed signing, service-account, or backend secrets in the client. Treat client receipts and integrity signals as input to validation, not authority.

## Required state matrix

Prove on the exact candidate: success, duplicate callback/delivery, pending, cancel, offline, verification/acknowledgement timeout and retry, refund/revoke, reinstall/restore, account mismatch, and backend outage. A consumable grants once even after callback replay; a pending/canceled/unverified purchase grants nothing; durable ownership restores; revoked ownership stops granting and is reconciled without corrupting unrelated progress. Test sandbox differences explicitly and do not describe an SDK/API that was not actually integrated.

Run `scripts/commerce_entitlement_probe.py`, then complete `assets/commerce-entitlement-review.template.md` with an independent security/operations review. Pricing, tax, disclosures, age requirements, and store policy remain platform/legal decisions, not assumptions by this skill.

## Primary references

- [Google Play Billing integration](https://developer.android.com/google/play/billing/integrate.html)
- [Google Play Billing security](https://developer.android.com/google/play/billing/security)
- [Apple StoreKit current entitlements](https://developer.apple.com/documentation/storekit/transaction/currententitlements)
