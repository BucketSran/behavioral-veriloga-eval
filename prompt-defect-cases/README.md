# Prompt Defect Cases

This directory archives benchmark prompts that were found to be ambiguous,
internally inconsistent, or polluted by duplicated text during clean A
baseline analysis.

It is intentionally outside `tasks/`, so normal generation runners do not read
these files.

## Source Of Truth

- Clean prompts for future runs live in `tasks/**/prompt.md`.
- Archived problematic prompts live under `prompt-defect-cases/cases/*/polluted_prompt.md`.
- Case notes live in `prompt-defect-cases/cases/INDEX.md`.

## What Counts As Prompt Pollution

- Repeated prompt fragments that distract the model.
- Missing output-format requirements, such as no required fenced `spectre`
  block for a testbench-generation task.
- Missing public artifact contracts, such as required file names,
  `ahdl_include` lines, module names, port order, or instance lines.
- Internal conflicts between the task text and the public evaluation contract.

## Boundary

Prompt cleanup may add public interface and artifact information needed to make
the task executable. It must not add checker source, hidden thresholds, private
gold implementation details, or post-hoc behavioral answers.

## Validation

The first four archived cases were cleaned in `tasks/**/prompt.md` and rerun:

- Generated root: `generated-A-prompt-cleanup-p0-kimi-2026-04-27`
- Result root: `results/A-prompt-cleanup-p0-kimi-2026-04-27`
- Result: `4/4 PASS`
- Hygiene: `generated=4`, `dry_run=0`, `placeholder=0`

After a broader static audit, nine more tb-generation prompts with repeated
`DUT module to instantiate` lines were archived and cleaned. The 13 cleaned
cases were rerun together:

- Generated root: `generated-A-prompt-cleanup-all13-kimi-2026-04-27`
- Result root: `results/A-prompt-cleanup-all13-kimi-2026-04-27`
- Result: `13/13 PASS`
- Hygiene: `generated=13`, `dry_run=0`, `placeholder=0`

The full prompt set was then statically audited:

- `DUT module to instantiate:` repeated pollution: 0 active prompts
- `injected Strict EVAS Validation Contract`: 0 active prompts
- repeated non-empty lines appearing at least four times: 0 active prompts
- end-to-end/tb-generation prompts missing explicit Spectre/code-block cue: 0

A full92 clean A rerun with the cleaned prompt set is available at
`results/clean-A-promptonly-kimi-2026-04-27-r2-promptclean`: `34/92`. This
full run confirms artifact hygiene (`generated=92`, `dry_run=0`,
`placeholder=0`) and `tb-generation=11/11`, but also shows model-output
trajectory variance in unrelated end-to-end tasks. Therefore the prompt cleanup
result should be interpreted as prompt/spec hygiene validation, not as a
monotonic full92 Pass@1 improvement claim.

Two follow-up prompt/interface probes were then run on the clean-A R2 failures:

- `results/A-infra-zero-kimi-2026-04-27`: the two prior `FAIL_INFRA` cases now
  produce ordinary compile/simulation feedback instead of missing generated
  artifacts.
- `results/A-linkage-promptfix-kimi-2026-04-27`: four linkage-looking
  `FAIL_DUT_COMPILE` cases pass after public artifact/interface prompt fixes
  (`4/4 PASS`).

Prompt hygiene policy was tightened in
`prompt_hygiene_audit_2026-04-27.md`: active prompts now prefer generic
Spectre/Verilog-A compatibility wording over concrete negative examples copied
from failed model outputs. The cleaner wording is the adopted prompt style even
when a concrete negative example would improve one local probe.

The latest prompt-only generic-hygiene full92 snapshot is:

- Generated root: `generated-clean-A-promptonly-kimi-2026-04-27-r3-genericprompt`
- Result root: `results/clean-A-r3-runnerfix-full92-2026-04-28`
- Result: `40/92 PASS`
- Hygiene: `generated=92`, `dry_run=0`, `placeholder=0`, `tb-generation=11/11`
- One remaining infra case comes from response truncation before emitting a
  required `.scs` testbench.

This `40/92` is the current active prompt baseline snapshot after runner/checker
rescore. Older R1/R2 runs used different prompt snapshots and are kept only as
prompt-cleanup history, not as main paper comparisons. Final paper claims should
estimate uncertainty by repeating the same frozen R3 prompt configuration in
fresh generated roots.
