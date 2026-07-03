# Raw Notes — Widget Sync Weekly Sync

Date: 2026.06.15
Recorder: Priya Shah

## Who was in the room

- Priya Shah (Engineering)
- José Peña (Product)
- Dana Lee (Product)
- Sam Okoro (Engineering)

## What we covered

1. Status of the depot API polling change (carried over from last week).
2. Billing dispute audit follow-up.
3. Scope check for the mobile app delta push.

## Notes as they happened

Sam gave a status update on the depot API polling change: the five-minute poll interval is
implemented against staging and passing the existing integration tests. José asked whether
we had re-run the billing dispute audit against the new polling behavior; Dana confirmed the
audit team re-sampled 40 tickets from the last two weeks and found zero new telemetry
mismatches, down from the prior sample's error rate.

The team decided to move the depot API polling change to production behind a feature flag,
rather than a full rollout, so it can be disabled quickly if the mobile app delta push
surfaces unexpected load. José raised the mobile app delta push scope: the current plan
pushes every changed widget record on every poll cycle, which José flagged as unnecessary
load on the mobile clients. The team decided to scope the delta push down to only widgets
whose reading changed since the last successful sync, deferring the "push all fields"
behavior to a later release.

Action items came out of this: Sam Okoro will land the feature flag for the polling change
by end of week. José Peña will draft the reduced delta-push spec and share it with the team
before the next sync. Dana Lee will re-run the billing dispute audit once the feature flag
is live in production, to confirm the mismatch rate holds at zero.

Before wrapping, the team flagged that the next sync should open with a review of production
metrics once the feature flag is live, and that the reduced delta-push spec is the first
agenda item once José's draft is ready.
