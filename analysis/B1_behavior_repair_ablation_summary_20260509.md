# B1 Behavior Repair Ablation Summary - 2026-05-09

## Current Status

The first B1 behavior-repair smoke ablations have been run and preserved.  The
current project decision is to use EVAS as the provisional B1 behavior standard
until the Virtuoso/Spectre bridge is stable again.  Under this EVAS-only
standard, the strict-output/retry variant is the best current mechanism: it
improves both candidate completeness and EVAS pass rate.  Spectre comparison is
deferred and its current results are treated as infrastructure-blocked because
both candidate and gold Spectre runs fail with SSH/upload banner timeouts.

The runner was also corrected during this cycle:

- Added `--freeze-dut-on-behavior` for TB-side behavior repair, so generated DUT
  files can be preserved while only generated testbenches are repaired.
- Fixed `_freeze_gold_harness` so DUT-side behavior repair no longer leaks gold
  `.va` DUT files into samples where the model produced no candidate DUT.
- Added strict code-output and artifact-retry switches for adaptive repair, so
  truncated missing-artifact responses can be retried with a code-only prompt.
- Updated Spectre validation to classify remote upload/SSH timeout as
  `FAIL_INFRA` rather than `FAIL_DUT_COMPILE`.
- Updated candidate staging to prefer the Verilog-A file named by the gold
  testbench `ahdl_include` when a sample contains multiple `.va` files.
- Main120 behavior validation must use `validate_benchmark_v2_gold.py`, not the
  adaptive runner's old internal `score.py` path, because the Main120 B1 tasks
  rely on task-local `checker.py` logic.

## Valid Smoke Results

All rows below validate materialized `adaptive_round1` candidates with
`validate_benchmark_v2_gold.py`.

| Run | Scope | Backend | Result | Pass tasks | Result root |
| --- | --- | --- | ---: | --- | --- |
| full-form-routed DUT / MiMo / 8192 / fixed | 8 DUT tasks | EVAS | 0/8 | none | `results/b1-ablation-full-dut-mimo-mt8192-fixed-round1-evas-20260509` |
| no-skill DUT / MiMo / 8192 / fixed | 8 DUT tasks | EVAS | 1/8 | `vbm1_vco_phase_integrator_dut` | `results/b1-ablation-noskill-dut-mimo-mt8192-fixed-round1-evas-20260509` |
| no-contract DUT / MiMo / 8192 / fixed | 8 DUT tasks | EVAS | 1/8 | `vbm1_edge_detector_dut` | `results/b1-ablation-nocontract-dut-mimo-mt8192-fixed-round1-evas-20260509` |
| no-skill + no-contract DUT / MiMo / 8192 / fixed | 8 DUT tasks | EVAS | 1/8 | `vbm1_edge_detector_dut` | `results/b1-ablation-noskill-nocontract-dut-mimo-mt8192-fixed-round1-evas-20260509` |
| strict + retry + no-skill + no-contract DUT / MiMo / 8192 | 8 DUT tasks | EVAS | 2/8 | `vbm1_edge_detector_dut`, `vbm1_vco_phase_integrator_dut` | `results/b1-ablation-strict-retry-noskill-nocontract-dut-mimo-mt8192-round1-evas-20260509` |
| strict + retry + no-skill + no-contract DUT / MiMo / 32768 | 8 DUT tasks | EVAS | 2/8 | `vbm1_edge_detector_dut`, `vbm1_vco_phase_integrator_dut` | `results/b1-ablation-strict-retry-noskill-nocontract-dut-mimo-mt32768-round1-evas-20260509` |
| compact-controller runner smoke / MiMo / 32768 | 3 DUT tasks | EVAS | 2/3 | `vbm1_edge_detector_dut`, `vbm1_resettable_counter_divider_dut` | `results/b1-compact-controller-runner-smoke-mimo-mt32768-evas-20260509` |
| full-form-routed TB / MiMo / 8192 / fixed | 2 TB tasks | EVAS | 0/2 | none | `results/b1-ablation-full-tb-mimo-mt8192-fixed-round1-evas-20260509` |
| strict + retry EVAS-positive audit | 2 DUT tasks | Spectre | 0/2 infra | none | `results/b1-ablation-strict-retry-noskill-nocontract-dut-mimo-mt8192-round1-spectre-jin-classified-20260509` |
| gold edge-detector infra check | 1 gold task | Spectre | 0/1 infra | none | `results/b1-spectre-infra-gold-edge-detector-jin-classified-20260509` |

## Interpretation

1. Full form-routed repair is not yet effective on this smoke set.  It produced
   valid code for four DUT tasks and no extracted code for four DUT tasks, but
   EVAS pass count remained 0/8.
2. Removing the repair skill improved one DUT task under EVAS:
   `vbm1_vco_phase_integrator_dut`.  Spectre then failed the same candidate with
   `FAIL_DUT_COMPILE`, so this is a useful ablation signal but not an accepted
   repair.
3. Removing contract diagnosis improved a different DUT task under EVAS:
   `vbm1_edge_detector_dut`.  Spectre also failed this candidate with
   `FAIL_DUT_COMPILE`.
4. Combining no-skill and no-contract did not stack the two benefits.  It kept
   the edge-detector EVAS positive, lost the VCO EVAS positive, and also failed
   the Spectre audit because of infrastructure.
5. Adding strict code output plus truncation retry improved the B1 smoke to EVAS
   2/8 and reduced no-code extraction from 4/8 to 1/8 relative to the previous
   no-skill + no-contract run.  The remaining no-code task was
   `vbm1_resettable_counter_divider_dut`.
6. Raising the token ceiling to 32768 confirmed that token budget was a
   confounder for artifact production: `vbm1_resettable_counter_divider_dut`
   changed from no-code/missing DUT to a runnable behavior failure.  EVAS pass
   count stayed 2/8, so larger token budget fixes candidate completeness but is
   not itself a behavior-repair mechanism.
7. Compact-controller runner mode is now implemented and reproducible.  On a
   3-task smoke it kept the existing `edge_detector` pass, repaired
   `resettable_counter_divider` to official EVAS PASS, and still failed
   `first_order_lowpass` with a runtime artifact error.  This supports using
   compact-controller as a token/artifact controller, not as a complete analog
   behavior strategy.
8. Provider wall time remains a separate bottleneck.  The resettable prompt was
   only 5252 characters but still took 358.925 seconds, so high token ceilings
   plus compact prompts should be paired with wall-time controls in the next
   loop.
9. The Spectre evidence is currently `INFRA_BLOCKED`, not candidate rejection:
   gold `vbm1_edge_detector_dut` also failed with
   `Connection timed out during banner exchange`.
10. The safe loop remains EVAS screen first, then immediate Spectre audit for
   every EVAS-accepted candidate before claiming success; the audit must only be
   considered decisive when it returns a real Spectre returncode and `tran.csv`.
11. TB-side repair generated code for both TB smoke tasks, but the offset
   comparator failed TB parsing because of an uncontinued multiline PWL source,
   and the segmented DAC failed correctness.

## Invalid Or Superseded Attempts

| Attempt | Status | Why retained |
| --- | --- | --- |
| `results/b1-ablation-full-dut-evas-20260509` | `BLOCKED_API` | Bailian/Kimi key expired; prompts and failure logs retained. |
| `results/b1-ablation-full-dut-mimo-evas-20260509` | `SUPERSEDED` | Initial MiMo provider setup failed before the key was added. |
| `results/b1-ablation-full-dut-mimo-mt8192-round1-evas-20260509` | `INVALID_SUPERSEDED` | Exposed gold-DUT leakage when no generated DUT existed; do not use for claims. |

## Preserved Artifacts

- Plan: `analysis/B1_behavior_repair_ablation_plan_20260509.md`
- Tracker: `analysis/B1_behavior_repair_ablation_tracker_20260509.md`
- Commands: `analysis/B1_behavior_repair_ablation_commands_20260509.md`
- DUT tasklist: `tasklists/B1_behavior_repair_dut_smoke_20260509.txt`
- TB tasklist: `tasklists/B1_behavior_repair_tb_smoke_20260509.txt`
- Runner patch: `runners/run_adaptive_repair.py`
- Spectre validator patch: `runners/validate_benchmark_v2_gold.py`
- Prompt-controller finding:
  `analysis/B1_prompt_controller_finding_20260509.md`
- Compact-controller smoke tasklist:
  `tasklists/B1_compact_controller_smoke_20260509.txt`
- Compact-controller unit test:
  `tests/test_compact_controller_repair.py`

## Next Step

Run the next EVAS-only smoke wave while Spectre is infrastructure-blocked:

- Keep strict code output enabled for B1 DUT repair; it is the first mechanism
  with both higher completeness and higher EVAS pass count.
- Treat token ceiling as a resource budget, not an ablation mechanism.  Use a
  high ceiling for B1 repair and compare fixed behavior loops/injection content.
- Use compact-controller fallback for artifact/runtime blockers.  The runner
  mode reduced prompts from 12k-16k chars to about 5.2k-5.4k chars and produced
  complete artifacts, but first-order still failed; this isolates generation
  control from behavior correctness.
- For `vbm1_resettable_counter_divider_dut`, move from artifact recovery to a
  targeted behavior repair: ratio=5 produced 40 output edges from 80 input edges,
  indicating divide-by-2 behavior rather than divide-by-5 behavior.
- TB repair prompt hardening for multiline Spectre source syntax, especially PWL
  continuation.
- Revisit Spectre comparison after the bridge is rebuilt; do not use current
  Spectre infra failures to rank candidates.
