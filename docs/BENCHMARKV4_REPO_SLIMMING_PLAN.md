# benchmarkv4 repository slimming plan

> **Historical document — not a current operating guide.**
> Use the [current documentation](README.md) for VABench r53 + EVAS 0.8.7.
> This pre-r53 proposal is retained as history, not as proof that every step was completed.

This note records the intended follow-up cleanup now that the benchmarkv4
release package has landed. It is deliberately a plan, not a deletion PR: the
repository should keep benchmark review, runner updates, and historical cleanup
in separate small changes.

## Goals

- Make the active benchmark entrypoint obvious.
- Keep the benchmark release package independent from experiment harnesses.
- Reduce accidental use of v1/v3 runner paths for benchmarkv4 experiments.
- Preserve historical evidence until it has a named archival path or a
  replacement report.

## Target layout

The benchmarkv4 release package is now accepted. The public root should evolve
toward:

```text
behavioral-veriloga-eval/
  benchmark-vabench-release-v4/
    release/
      benchmarkv4/
        MANIFEST.json
        TASK_INDEX.json
        prompt_modes/
        tasks/
    provenance/
      dut-base-v3-exact-five-hash-bound-v2/
    operations/
      tri_form_derivation_prep/

  runners/
    run_benchmarkv4_model_eval.py
    ...

  docs/
  schemas/
  scripts/
  tests/

  benchmark-vabench-release-v3/   # legacy previous active release
  benchmark-vabench-release-v1/   # legacy evidence / website surface
  examples/
```

The `benchmark-vabench-release-v4/release/benchmarkv4/` tree should remain the
benchmark package. It should not contain model API credentials, raw model
outputs, transient simulator runs, or ad hoc experiment logs.

## Runner cleanup

The next model-evaluation runner should be benchmarkv4-native:

- read `benchmark-vabench-release-v4/release/benchmarkv4/TASK_INDEX.json`;
- select tasks by task id, form, prompt mode, or limit;
- call
  `benchmark-vabench-release-v4/operations/tri_form_derivation_prep/export_tri_form_runtime.py`
  for prompt/runtime materialization;
- send the materialized prompt to an OpenAI-compatible or Anthropic-compatible
  API endpoint;
- write generated candidates and token/accounting metadata under an ignored
  output directory selected by the caller;
- optionally hand the generated artifact to EVAS or Spectre judging in a later
  stage.

The runner should not reimplement prompt concatenation. Runtime export remains
the single source of truth for G0-G5 prompt composition, wrapper/skill ordering,
and public/private separation.

Older v1/v3 model runners can remain temporarily, but should be labelled as
legacy once a benchmarkv4 runner exists.

## Skill directory treatment

The current top-level `skills/` directory contains agent-facing helper notes.
Those files are not part of the benchmarkv4 task definition, prompt mode
surface, or evaluator. After the v4 release lands, handle this directory in a
small follow-up PR:

- either move the material under documentation, such as `docs/agent_guides/`;
- or keep `skills/` but describe it as optional agent guidance, not release
  content.

Do not mix that decision with benchmark package changes.

## Suggested PR sequence

1. Land benchmarkv4 release/package PRs. (complete)
2. Update README and repository layout policy to point new work at
   `benchmark-vabench-release-v4/release/benchmarkv4/`.
3. Add the benchmarkv4-native model API runner and dry-run tests.
4. Mark v1/v3 model runners as legacy or move them under a legacy namespace.
5. Reclassify or move top-level agent skill notes.
6. Archive or remove historical report surfaces only after their remaining
   references are audited.

Each step should be reviewable on its own. Broad deletion should only happen
after the replacement entrypoint and runner are available.
