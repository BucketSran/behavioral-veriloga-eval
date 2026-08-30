# AA-VAE-048 — Record ledger and bounded generated comparisons

Status: integrated into read-only native scoring; actual retry and Reasoning
Docker campaigns verify export. This does not generate formal model claims.

## Idea / reference

The public AlphaApollo architecture motivates recording complete multi-step
trajectories instead of only final answers (public commit
`712a04dcdefb0eabdb6622350460f187e9bb5941`, `workflows/api.py`, Apache-2.0).
The ledger, denominator rules and claim gates here are vaEVAS-specific; no
third-party source code was copied.

## Code and use

- `benchmark-vabench-release-v4/operations/calibration_pilot/result_ledger.py`
  projects already verified native rows without executing models or judges.
- `score_campaign.py --ledger-output /absolute/path/new-reviewer-ledger.json`
  generates a separate write-once reviewer ledger and links its file/content
  hashes from the existing private report. The output must be outside generation
  evidence and cannot replace the campaign or score report.
- Exact frozen schedule joins preserve every cell, null infrastructure scores,
  selected attempt and all-attempt costs. Unknown usage is null with known
  subtotals and unknown counts, never a zero-cost failed attempt.
- Matched comparisons require backend/task/form/model/repetition identity and
  show missing/ineligible arms. Effective model/repetition may derive from the
  frozen top-level campaign or scheduled cell, with explicit provenance.
- Only named single-trajectory arms and native mini-swe/Reasoning are accepted.
  Evolution/candidate-only/unknown backends and unannounced mixtures fail closed.
  Numeric scores without bound authority are not eligible. Deadline and
  post-deadline outcomes are separate analyses.
- Safe projection excludes prompts, raw responses, tool output and hidden
  diagnostic text. Claim index explicitly disallows automatic model-quality
  claims; development-only/connectivity evidence is not a paper result.

## Verification

Tests: `test_agent_harness_result_ledger.py`,
`test_agent_harness_ledger_integration.py`, existing native/attempt/score-reuse
tests and nine-cell smoke with actual external ledger output. Independent review
repaired mixed-backend pairing and real campaign top-level model compatibility;
final integration review found no blocker.

The ordinary private score report remains available without a ledger flag.
Evolution has a different estimand and requires its own explicit result index;
this ledger intentionally does not accept it by relabeling its conditions.
