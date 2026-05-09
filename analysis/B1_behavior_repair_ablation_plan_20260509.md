# B1 Behavior Repair Ablation Plan - 2026-05-09

## Purpose

Run a first EVAS-fast ablation suite for B1 behavior repair on the 10 selected
compile-clean S2 behavior failures.  The source candidates are the MiMo S2
artifacts, mirrored under `generated-b1-source-mimo-s2-as-kimi/kimi-k2.5` so the
available Bailian-backed repair model can run without altering the original S2
tree.

## Source Split

- DUT-side behavior tasks:
  `tasklists/B1_behavior_repair_dut_smoke_20260509.txt`
- TB-side behavior tasks:
  `tasklists/B1_behavior_repair_tb_smoke_20260509.txt`
- Original combined smoke list:
  `tasklists/B1_behavior_repair_smoke_20260509.txt`

## First-Round Ablations

| Variant | DUT-side command flag | TB-side command flag | What it tests |
| --- | --- | --- | --- |
| `full-form-routed` | `--freeze-gold-harness-on-behavior` | `--freeze-dut-on-behavior` | Whether form-aware behavior repair improves metrics without compile regression. |
| `no-skill-form-routed` | above + `--no-repair-skill` | above + `--no-repair-skill` | Contribution of mechanism/repair skill guidance. |
| `no-contract-form-routed` | above + `--disable-contract-diagnosis` | above + `--disable-contract-diagnosis` | Contribution of task-local behavior contract diagnosis. |
| `no-routing` | none | none | Whether DUT/TB surface routing prevents wrong-layer edits and regressions. |

## Early Acceptance Rule

EVAS is the fast screen for this first smoke.  A candidate is considered useful
only if it preserves compile, improves checker metrics or reaches PASS, and does
not lose previously working public artifact surfaces.  Any EVAS-accepted B1
candidate must later receive targeted Spectre audit before paper-facing claims.

## Result Roots

All first-round outputs use:

- generated roots: `generated-b1-ablation-*`
- EVAS result roots: `results/b1-ablation-*`
- summary artifact: `analysis/B1_behavior_repair_ablation_summary_20260509.md`
