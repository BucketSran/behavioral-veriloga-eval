# vaBench v3 Evaluator Contract

> **Historical document — not a current operating guide.**
> Use the [current documentation](README.md) for VABench r53 + EVAS 0.8.7.
> This is the V3 protocol only; it does not define current r53 judge authority or runtime requirements.

Updated: 2026-08-29

This document is the executable boundary for v3 generation, private hidden
scoring, evidence retention, and model-score claims. Pinned strict EVAS is the
formal judge. Spectre is optional parity evidence and is never a release,
certification, or model-score dependency.

## Pinned environment

The machine-readable source of truth is
`environment/evaluator-contract.json`. The project and CI lock the evaluator
and test dependencies in `uv.lock`; the public agent image separately installs
`environment/requirements.lock` with `pip --require-hashes`.

Required evaluator identity:

- Python 3.11;
- `evas-sim==0.8.7`;
- canonical engine `evas-rust`;
- Rust core present and loadable;
- Rust core ABI `20260718` and core version `0.2.4`.

Create the locked local environment and emit live evidence:

```bash
uv sync --locked --group dev --python 3.11.13
uv run python scripts/verify_evaluator_environment.py \
  --run-evas \
  --evas-command evas \
  --json \
  > /tmp/vabench-evaluator-environment.json
```

The verifier fails closed on source-contract, package, engine, native-core,
ABI, or version mismatches. A static verifier run without `--run-evas` is
useful for repository checks but is not sufficient evidence for a formal
model-score claim.

## Clean-room hidden-scoring smoke

The smoke exposes exactly one public instruction, public starter artifacts,
and the candidate submission in a temporary clean room. Gold solutions,
hidden testbenches, checker routing, and the benchmark checkout remain on the
evaluator side.

```bash
uv run python scripts/run_v3_clean_room_smoke.py \
  --task 014 \
  --evas-command evas \
  --environment-evidence /tmp/vabench-evaluator-environment.json \
  --output-root /tmp/vabench-v3-clean-room-output \
  --out /tmp/vabench-v3-clean-room-smoke.json \
  --json
```

A passing report may support only the claim scope
`single_task_clean_room_pipeline`. It proves the selected generation adapter,
mount boundary, installed EVAS identity, private hidden scorer, result writer,
and cleanup path executed successfully. It does not support a model-quality or
aggregate benchmark-score claim.
If scoring passes but the environment/cleanup claim gate is blocked, the smoke
still writes its report and exits with status 2.

## Full v3 evaluation entrypoint

For the current exploratory candidate surface:

```bash
uv run python runners/run_vabench_v3_model_eval.py \
  --stage all \
  --selection-surface candidate \
  --claim-scope exploratory_candidate_eval \
  --evas-command evas \
  --environment-evidence /tmp/vabench-evaluator-environment.json \
  --model <model-id> \
  --api-key-file <credential-path> \
  --output-root results/<run-id> \
  --json
```

The command records input hashes, selected denominator rows, every terminal
score status, per-result hashes, candidate/hidden-test identities, EVAS
identity, failure class, and the claim gate. Credentials are inputs to the
model API only and must never be copied into the output tree.

Formal model-score reporting uses the same entrypoint with:

```text
--selection-surface counted --claim-scope formal_model_score
```

That scope remains blocked until the score roster contains a non-empty frozen
`counted_in_score=true` denominator. A formal score requires the entire
unfiltered counted surface from the canonical repository roster, one terminal
hidden-score result for every row, matching input/result hashes, a clean
repository identity, Python exactly `3.11.13`, matching live and per-run EVAS
identities, the same EVAS command recorded by environment verification,
persistent-worker mode disabled, and no infrastructure failures. Candidate
compile or behavioral failures stay in the denominator as zero-score outcomes;
they are not dropped or replaced by retries. A blocked formal run, including an
empty denominator, writes its summary and exits with status 2.

## Failure and ownership boundary

- `candidate`: deterministic DUT compile, testbench compile, or behavioral
  correctness failure. It is a valid scored outcome.
- `infrastructure`: missing candidate/result, missing private testbench,
  evaluator exception, invalid identity, absent/unloadable native core, or
  other failure that prevents a valid score. It blocks formal claims.
- EVAS package/compiler/simulator changes belong in the EVAS fork only after
  live package/native identity passes and an isolated supported-language case
  reproducibly fails after entering the EVAS compiler or simulator.
- Benchmark selection, clean-room boundaries, checker policy, denominator,
  evidence indexing, and claim gating belong in this repository.

The CI workflow `.github/workflows/evaluator-closure.yml` executes the live
environment verifier, focused tests, and the one-task hidden-scoring smoke.
