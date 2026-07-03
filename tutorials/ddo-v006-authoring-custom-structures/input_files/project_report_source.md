# Atlas Platform Migration — Raw Status Notes

These are the unedited status notes collected from the program's weekly sync, exported from
the tracking board and the on-call metrics dashboard. They are the raw source material a
`project_report` document should trace its metrics, risks, and milestone statuses to — nothing
in the rendered report should state a figure or a claim that cannot be found below.

## Program

- Project: Atlas Platform Migration (legacy billing datastore -> managed Postgres cluster).
- Reporting window: 2026.06.01 through 2026.06.28.
- Program lead: Priya Nandakumar.
- Steering sponsor: Marcus Webb (VP Engineering).

## Milestone board (as exported 2026.06.28)

- Milestone 1: "Schema parity audit" — closed 2026.05.30. All 42 legacy tables mapped to the
  new schema; 0 open discrepancies at close.
- Milestone 2: "Dual-write shim in production" — closed 2026.06.10. Shim has written to both
  stores for 18 consecutive days with 0 write divergences detected by the reconciliation job.
- Milestone 3: "Data migration dry run" — closed 2026.06.15. Dry run moved 100% of the
  staging dataset (2.3 TB) in 6 hours 40 minutes against a planned 8-hour window.
- Milestone 4: "Production cutover rehearsal" — in progress. As of 2026.06.28, 3 of 5
  rehearsal steps are complete (schema freeze drill, read-replica promotion drill, and
  rollback drill). The remaining 2 steps (live traffic shadow test, final cutover timing
  run) are scheduled for the week of 2026.07.06.
- Milestone 5: "Legacy datastore decommission" — not started. Blocked on Milestone 4
  completion; no date has been set.

## Metrics dashboard export (2026.06.28)

- Reconciliation job write-divergence count: 0 divergences across 18 days of dual-write
  (2026.06.10 - 2026.06.28).
- Dry-run migration duration: 6 hours 40 minutes for 2.3 TB, against an 8-hour target window
  (Milestone 3, 2026.06.15).
- On-call incident count attributable to the migration workstream during the reporting
  window: 1 (a read-replica lag alert on 2026.06.22, resolved in 40 minutes, no customer
  impact).
- Rehearsal drill pass rate: 3 of 3 completed rehearsal steps passed acceptance criteria on
  first attempt (schema freeze, read-replica promotion, rollback).

## Risk log (open items as of 2026.06.28)

- R-1: The managed Postgres vendor's committed support SLA for the go-live weekend has not
  yet been countersigned; procurement flagged a 2-week delay in legal review on 2026.06.20.
  Owner: Marcus Webb (steering sponsor).
- R-2: The live traffic shadow test (Milestone 4, step 4) requires a second on-call engineer
  who is currently allocated to an unrelated incident-response rotation through 2026.07.03.
  Owner: Priya Nandakumar.
- R-3: The rollback drill (completed 2026.06.24) took 22 minutes against a 15-minute target;
  the runbook has not yet been updated to close that gap. Owner: David Chen (SRE).

## Notes from the 2026.06.28 sync (verbatim excerpts)

- Priya: "We're still on pace for a late-July cutover window if the SLA countersignature
  lands by 2026.07.10. If it slips past that, we lose the July maintenance window entirely
  and push to September."
- Marcus: "I need a clear ask from this group on whether we escalate the SLA countersignature
  to legal leadership this week or wait one more cycle."
- David: "Rollback drill timing is the one number I'm not happy with. 22 minutes isn't
  terrible, but it's the only rehearsal step that missed its target, and I want the runbook
  fix in before we run the shadow test."
