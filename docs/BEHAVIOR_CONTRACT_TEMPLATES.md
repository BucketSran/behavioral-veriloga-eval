# Behavior Contract Templates

This document defines the first vaEvas behavior-contract layer for improving
EVAS-guided repair after H-on-F.  These contracts are not a replacement for the
existing checkers.  They are a repair-facing diagnostic layer that turns coarse
`FAIL_SIM_CORRECTNESS` results into smaller behavior facts.

## Guardrail

Gold contracts are judge-side artifacts.  During benchmark repair, do not paste
hidden numeric windows, exact expected sequences, or checker source into the LLM
prompt.  The LLM should receive only an abstract diagnostic summary, such as:

```text
Passed: reset release and input stimulus activity.
Failed: output clock activity; no feedback edges were produced.
Repair scope: DUT behavior only. Preserve module name, ports, and harness.
```

## Contract Schema Sketch

```json
{
  "task_id": "example_task",
  "contracts": [
    {
      "name": "output_edges_present",
      "type": "edge_count",
      "severity": "hard",
      "signal": "fb_clk",
      "min_edges": 8,
      "diagnostic_hint": "feedback clock is not oscillating",
      "repair_family": "clock-event-generator-or-reset-release"
    }
  ]
}
```

Legacy sketch:

```yaml
contracts:
  - name: output_edges_present
    type: edge_count
    signal: fb_clk
    min_edges: 8
    window: post_reset
    diagnostic_hint: "feedback clock is not oscillating"
```

Common fields:

- `name`: stable contract identifier.
- `type`: one of the templates below.
- `severity`: `hard` or `advisory`. Missing severity is treated as `hard`
  for backward compatibility.
- `signals`: task-visible signal names or aliases.
- `window`: abstract window name or public time range.
- `diagnostic_hint`: repair-facing summary.  Keep this generic.
- `repair_family`: maps the contract to a repair mechanism family.

## Automated Generation

The reusable generator is:

```bash
python3 runners/generate_behavior_contracts.py \
  --triage-json results/behavior-contract-triage-H-on-F-stable-2026-04-26.json \
  --out-root results/generated-behavior-contracts-H-on-F-stable-2026-04-26-v3
```

It instantiates templates from:

- checker-required columns when they can be extracted safely;
- gold harness save names;
- task prompt public waveform columns;
- failed-run `tran.csv` headers;
- EVAS notes and triage failure family;

Generated contracts use two severity levels:

- `hard`: likely behavior-correctness requirements. Hard failures make
  `contract_check.py` return `FAIL_CONTRACT`.
- `advisory`: useful repair hints such as input/stimulus coverage. Advisory
  failures remain visible in repair prompts but do not make an otherwise
  hard-clean candidate fail the contract layer.

The generator writes contracts outside task directories by default.  Repair
experiments can opt in with:

```bash
VAEVAS_CONTRACT_ROOT=results/generated-behavior-contracts-H-on-F-stable-2026-04-26-v3 \
python3 runners/run_adaptive_repair.py ...
```

If `VAEVAS_CONTRACT_ROOT` is unset, repair prompts fall back to task-local
`contracts.json`.

## Template Families

### `runtime_csv_exists`

Use when EVAS/Spectre preflight passes but no useful transient artifact is
available, or a checker times out.

Repair family: `runtime-interface-minimal-harness`

Diagnostic summary:

- waveform CSV is absent, empty, or too expensive for the checker;
- fix include paths, instance wiring, tran setup, save list, and stimulus;
- do not tune behavior constants until the runtime artifact exists.

### `edge_count`

Use when the design should emit clock, pulse, data, or state-transition edges.

Repair family: `clock-event-generator-or-reset-release`

Typical checks:

```yaml
- type: edge_count
  signal: clk_out
  min_edges: 4
  window: after_reset
- type: edge_count
  signal: data_edge
  min_edges: 1
  window: stimulus_active
```

Diagnostic summary:

- expected edges are absent or too sparse;
- check reset release, event scheduling, `timer()` cadence, and output drive;
- preserve any already-working harness and module interface.

### `frequency_ratio`

Use for divider, oscillator, PLL, and ratio-hop tasks.

Repair family: `pll-dco-counter-feedback-loop`

Typical checks:

```yaml
- type: frequency_ratio
  reference: ref_clk
  feedback: fb_clk
  expected_ratio: 1.0
  tolerance: 0.35
- type: high_fraction
  signal: lock
  min_fraction: 0.05
```

Diagnostic summary:

- feedback edges exist but cadence or lock behavior is wrong;
- repair counter thresholds, DCO period update, lock detector, or hop handling;
- avoid changing public ratio-code interface.

### `code_coverage`

Use for ADC, DAC, quantizer, SAR, and digital code output tasks.

Repair family: `clocked-quantizer-code-update`

Typical checks:

```yaml
- type: input_span
  signal: vin
  min_span_class: covers_codes
- type: code_coverage
  bits: [dout_2, dout_1, dout_0]
  min_unique_codes: 4
- type: monotonic_code
  input: vin
  code: dout
```

Diagnostic summary:

- input stimulus is present but output code is stuck or incomplete;
- repair sampling event, quantizer thresholds, reset gating, or bit mapping;
- do not redesign the testbench if stimulus and clock contracts pass.

### `output_span`

Use when an analog output should move but is stuck at zero, supply, or a
constant value.

Repair family: `drive-output-target-and-transition`

Typical checks:

```yaml
- type: output_span
  signal: vout
  min_span: public_or_task_class
- type: activity_after_stimulus
  input: code
  output: vout
```

Diagnostic summary:

- decoded activity or input span exists, but analog output is not driven;
- repair target variable updates and `V(out) <+ transition(target, ...)`;
- confirm supply scaling and bit-weight mapping.

### `any_output_span`

Use for differential outputs where either side may carry the visible activity,
or the checker accepts activity on one of several monitor columns.

Repair family: `drive-output-target-and-transition`

Typical checks:

```yaml
- type: any_output_span
  signals: [VDAC_P, VDAC_N]
  min_span: 0.1
```

Diagnostic summary:

- output activity is absent across all accepted output columns;
- repair the differential/common-mode output target update;
- avoid requiring both sides to swing when the task checker only needs one
  visible active side or a differential activity proxy.

### `onehot_no_overlap`

Use for DWA, thermometer selection, and pointer/cell-enable tasks.

Repair family: `dwa-pointer-thermometer-mask`

Typical checks:

```yaml
- type: post_reset_samples
  signals: [ptr_0, cell_en_0]
  min_rows: 2
- type: active_count_range
  signals: cell_en_0..cell_en_15
- type: pointer_wrap
  signals: ptr_0..ptr_15
```

Diagnostic summary:

- pointer/cell-enable observability or wrap behavior is wrong;
- repair reset initialization, pointer increment, modulo wrap, and no-overlap mask;
- keep scalar observable aliases if they already exist.

### `pulse_width`

Use for PFD, BBPD, pulse generator, deadzone, and reset-race tasks.

Repair family: `pfd-latched-pulse-delayed-clear`

Typical checks:

```yaml
- type: pulse_width
  signal: up
  min_width_class: visible
  max_width_class: bounded
- type: mutual_reset_window
  signals: [up, dn]
- type: pulse_order
  cause: ref_edge
  effect: up_pulse
```

Diagnostic summary:

- pulse ordering, width, or mutual reset behavior is wrong;
- repair latch-on-edge logic, delayed clear timer, and reset priority;
- avoid rewiring the testbench when pulse observables are already present.

### `pulse_symmetry_window`

Use for PFD reset-race tasks where public `ref`/`div` edge order changes during
the run and both response sides must be exercised.

Repair family: `pfd-windowed-latched-pulse-symmetry`

Typical checks:

```yaml
- type: pulse_symmetry_window
  reference: ref
  feedback: div
  up: up
  down: dn
  min_pairs_per_side: 4
```

Diagnostic summary:

- reference-leading edge pairs should produce UP responses;
- feedback-leading edge pairs should produce DN responses;
- preserve any passing non-overlap behavior while fixing the missing side.

### `paired_edge_response`

Use as an advisory PFD/BBPD mechanism check. The checker dynamically pairs
nearby public reference/feedback edges and verifies that the leading side has a
matching output pulse.

Repair family: `pfd-windowed-latched-pulse-symmetry`

Typical checks:

```yaml
- type: paired_edge_response
  reference: ref
  feedback: div
  up: up
  down: dn
  min_response_fraction: 0.8
```

Diagnostic summary:

- edge detection is present, but latch/set/clear behavior may be asymmetric;
- do not require both states to be zero before setting the currently leading
  side;
- keep event controls unconditional and move conditional logic inside event
  bodies.

### `pulse_width_fraction_window`

Use as an advisory pulse-shape check for PFD-like tasks. It checks that the
expected side is visible but finite inside paired-edge response windows, while
the opposite side remains mostly low.

Repair family: `pfd-windowed-latched-pulse-symmetry`

Typical checks:

```yaml
- type: pulse_width_fraction_window
  reference: ref
  feedback: div
  up: up
  down: dn
  min_expected_fraction: 0.001
  max_expected_fraction: 0.6
```

Diagnostic summary:

- pulses should not be absent, static high, or cross-coupled to the wrong side;
- repair finite pulse target variables and delayed clear timing;
- avoid hidden numeric checker windows by deriving response windows from public
  edge pairs.

### `pulse_count`

Use when a pulse output must produce visible rising pulses rather than a static
level.

Repair family: `pfd-latched-pulse-delayed-clear`

Typical checks:

```yaml
- type: pulse_count
  signal: up
  min_pulses: 2
- type: pulse_count
  signal: dn
  min_pulses: 2
```

For `pfd_deadzone`-style tasks, only `up` may be required; `dn` can instead be
checked with a max high-fraction contract.

### `non_overlap`

Use for mutually exclusive pulse outputs such as `up/dn` or `up/down`.

Repair family: `pfd-latched-pulse-delayed-clear`

Typical checks:

```yaml
- type: non_overlap
  signals: [up, dn]
  max_overlap_fraction: 0.02
```

Diagnostic summary:

- both pulse outputs are high at the same time too often;
- repair delayed-clear/reset priority and make pulse target state mutually
  exclusive.

### `code_hamming_distance`

Use for Gray-code/state-machine tasks where consecutive observed states should
change by a bounded number of bits.

Repair family: `clock-event-generator-or-reset-release`

Typical checks:

```yaml
- type: code_hamming_distance
  bits: [g3, g2, g1, g0]
  max_hamming: 1
  min_transitions: 4
```

Diagnostic summary:

- state may be changing, but transitions violate the expected local property;
- repair state update or output encoding rather than only adding more clock
  edges.

## First Experiment Cut

Use the H-on-F stable triage report to select a small repair set:

- `missing_edges_or_clock_activity`: `adpll_timer_smoke`, `gray_counter_one_bit_change_smoke`
- `runtime_or_timeout`: `pfd_reset_race_smoke`, `sar_adc_dac_weighted_8b_smoke`
- `pll_or_ratio_tracking`: `cppll_timer`, `adpll_ratio_hop_smoke`
- `code_coverage_or_quantizer`: `adc_dac_ideal_4b_smoke`, `segmented_dac`
- `analog_output_stuck`: `dac_therm_16b_smoke`, `cdac_cal`
- `dwa_or_onehot_overlap`: `dwa_wraparound_smoke`, `dwa_ptr_gen_smoke`

For each task, write or generate a small JSON contract spec, run the existing
candidate through `runners/contract_check.py`, and feed only the diagnostic
summary into the next repair prompt.
