# Widget Sync Weekly Sync — Notes
**Meeting Notes**

* **Version:** 0.1.0
* **Date:** 2026.06.15
* **Status:** FINAL
* **Authors:** Priya Shah, Engineering

---


## Attendees

Priya Shah (Engineering) — José Peña (Product) — Dana Lee (Product) — Sam Okoro (Engineering).


## Agenda Covered

Depot API polling change status. Billing dispute audit follow-up. Scope check for the mobile app delta push.


## Decisions

Decided: ship the depot API polling change to production behind a feature flag rather than a full rollout. Decided: scope the mobile app delta push down to only widgets whose reading changed since the last successful sync, deferring the "push all fields" behavior.


## Action Items

Sam Okoro — land the feature flag for the polling change — by end of week. José Peña — draft the reduced delta-push spec — before the next sync. Dana Lee — re-run the billing dispute audit — once the feature flag is live in production.


## Next Steps

Open the next sync with a review of production metrics once the feature flag is live. First agenda item: the reduced delta-push spec, once José's draft is ready.




---
## Appendix: Evidence Bank


**ID:** `meeting_notes_source_20260615` (transcript)
**Source:** tutorials/ddo-v006-authoring-custom-structures/input_files/meeting_notes_source.md
**Content:** Raw notes from the 2026.06.15 Widget Sync Weekly Sync, including the attendee list, decisions on the feature-flagged polling rollout and scoped delta push, and the resulting action items.



