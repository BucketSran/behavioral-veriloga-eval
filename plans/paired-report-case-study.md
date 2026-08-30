# Paired reporting and reviewer-safe case index (AA-VAE-063)

Updated: 2026-08-31. Overnight queue N2. Independent read-only inventory/design
completed; implement against existing ledger coverage and score-eligibility rules.

## Scope and acceptance

Extend `build_native_campaign_ledger` with a report-ready `paired_summary` and
`case_study_index`. Reuse current records, pair coverage and hash projections;
no new dependencies, IO, renderers, scorer changes or alternative ledger.
Keep the current rejection of extension rows. Existing ledger hashes cover the
new projections and old records/claim boundaries remain unchanged.

- Arm summary: planned/observed/score-eligible/passed counts, pass rate over
  explicitly eligible cells (null at zero denominator), ineligible reasons.
- Pair summary: planned pair slots, matched eligible/skipped counts, skip
  reasons, left/right wins, ties, delta sum and mean (null at zero pairs).
  Never drop failed or missing planned cells from the coverage denominator.
- Case index: allowlisted identity/status/score/usage and evidence hash joins.
  Include available trajectory tail, submission tree, final profile/input and
  sidecar references from already validated rows; missing joins are listed as
  incomplete rather than inferred or loaded from disk.
- Do not project prompt, model output, raw trajectory, candidate source or
  private final-checker diagnostics. No statistical significance claim.

TDD: three arms with one infrastructure failure; all-pass ties; valid incomplete
arm coverage if the existing public API permits it; otherwise preserve schedule
rejection rather than manufacturing illegal rows. Cover complete/missing case
evidence and explicit malicious/raw-text leakage sentinels. Verify targeted
ledger tests and existing consumer tests; return independent review evidence.

## Exact ownership

`paired_report_impl` alone may edit calibration-pilot `result_ledger.py` and
`tests/test_agent_harness_result_ledger.py`. Main owns all docs/CI/Git and N1
launcher/scorer modules. Preserve others' changes. No worker commits, pushes,
shared schema edits, real data/provider access, EVAS/r53/old-worktree changes.
Hand back unstaged source/tests with RED/GREEN evidence and stop writing.
