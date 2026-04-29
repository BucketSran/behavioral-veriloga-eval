# Benchmark-v2 Draft Area

`benchmark-v2` is a staging area for harder VAEVAS perturbation benchmarks.  It
is separate from the official `tasks/` tree by design.

## Boundary Rules

- Draft tasks stay here until manifest, gold, checker, and EVAS/Spectre parity
  are reviewed.
- Do not migrate draft tasks into `behavioral-veriloga-eval/tasks/` during
  planning.
- Do not write generated model outputs or active result roots here.
- Do not report reused gold, R26, verified artifacts, or materialized
  teacher-derived templates as cold-start success.

## Intended Layout

```text
benchmark-v2/
  README.md
  manifests/
    v2-small.json
  tasks/
    <task_id>/
      prompt.md
      gold/
        dut.va
        tb_*.scs
      checker.py
      meta.json
```

The initial 30 task directories have now been materialized and gold-validated.
Each task contains:

- `prompt.md`
- `gold/dut.va`
- `gold/tb_ref.scs`
- `checker.py`
- `meta.json`

Gold validation roots:

- EVAS: `behavioral-veriloga-eval/results/benchmark-v2-gold-validation-2026-04-29-r2` (`30/30`)
- Spectre: `behavioral-veriloga-eval/results/benchmark-v2-gold-validation-spectre-2026-04-29-r1` (`30/30`)

These are gold correctness results only. They are not model-generation results.

## v2-small Design

`v2-small` is a 30-task manifest draft covering six mechanism groups:

- ADC-DAC chain with shared quantized state
- binary DAC versus thermometer/unit-cell distractors
- DWA pointer rotation and wrap behavior
- PFD reset race and lock-window behavior
- divider/counter ratio and encoding distractors
- sample/hold plus calibration/system composition

The split is intentionally harder than simple renames.  It includes semantic
aliases, keyword removal, negative constraints, parameter perturbations, and
small system compositions.

## Status Values

- `draft_manifest`: manifest entry exists, task files not authored
- `needs_gold`: prompt exists but gold DUT/testbench missing
- `needs_checker`: gold exists but checker missing or manual-only
- `needs_parity`: EVAS gold pass exists but Spectre parity not reviewed
- `reviewed_candidate`: ready for promotion review
- `promoted`: copied into official tasks by an explicit promotion action
- `validated_gold_evas_spectre`: prompt, gold, checker exist and gold passes EVAS + real Spectre

Current entries are `validated_gold_evas_spectre`.
