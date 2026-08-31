# Legacy native sensitivity: r53 public contract compatibility

2026-08-31. Base: `e5f2e9dceccf3435768ce4af5753c4b268d650fc`.

## Brief, KPI and scope

Close the separate residual identified by AA-VAE-067: the explicit
`--agent-scaffold native` sensitivity loop calls `run_campaign.run_public_evas`,
whose schema lists stop at r52 and whose suffix-only portable detection cannot
handle r53 reference-v1 Testbench contracts. This is not the default mini-swe
or the opt-in native controller/Reasoning/Evolution validator.

Primary KPI: released r53 strict and portable DUT, bugfix and reference-only
Testbench contracts reach the existing fixed-argv executor with correct flags.
Secondary KPIs: malformed r53 schema/mode/command/binding/case combinations
are rejected before execution; supported historical r45-r52 paths retain their
behavior. Test via the actual legacy `execute_tool("run_evas")` entry and a
subprocess fixture, not only parser assertions. Nonzero execution stays failed.

Reuse AA-VAE-067's canonical r53 contract selector; never execute metadata shell
commands. Keep the old public-only scratch/candidate checks and response shape.
No r53/EVAS 0.8.7 bytes, final judge, trajectory schema, selection/scoring policy,
model API call, real corpus, training, hidden inspection or old-worktree edit.
The pinned dynamic-array runtime limitation remains explicit and unchanged.

## Plan and ownership

1. Commit this intake separately; verify navigation and fork/upstream baseline.
2. Vertical RED -> GREEN for a released strict DUT contract, then portable
   reference Testbench; complete three-form strict/portable regression coverage.
3. Lock public authority rejection and historical behavior with focused tests.
   Run harness regression and static checks; independent read-only review.
4. Publish focused GREEN commits only to BucketSran fork/main; inspect the exact
   source's hosted full-checkout and Docker gates, then close evidence records.

Main alone owns calibration-pilot `run_campaign.py`, a focused legacy contract
test under `tests/test_agent_harness_*.py`, any necessary existing calibration
test changes, applicable calibration README, this plan/current-plan/ownership,
decision/verification logs and AA-VAE-068 feature/index. No delegated writes or
Git operations. `portable_contract_review` provides bounded read-only advice;
`portable_fix_review` independently reviews the final diff. Their earlier
writing assignments, if any, remain closed.

## Evidence and stop conditions

Record exact RED/GREEN and source-bound hosted evidence in verification-log.
The compact local checkout lacks old release assets; use synthetic historical
fixtures locally and the hosted full checkout for the historical broad gate.
Fake EVAS proves dispatch/flags/paths, not simulator success or isolation.
Hosted existing clean-room stages guard mainline trajectory/freeze/final joins;
do not describe them as a new legacy Docker or model-quality experiment.

Stop if a fix requires benchmark/evaluator/scoring changes, broader feedback,
credentials or paid calls. No dependency addition. LSP/typecheck unavailable
must be disclosed separately from Ruff/compilation/AST evidence.
