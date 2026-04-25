Write a Verilog-A module named `cross_hysteresis_window_ref`.

# Task: cross_hysteresis_window_smoke

## Objective

Write a Verilog-A hysteresis element that uses directional `cross()` events to switch HIGH and LOW at different thresholds.

## Specification

- **Module name**: `cross_hysteresis_window_ref`
- **Ports**: `vin`, `out`, `VDD`, `VSS` - all `electrical`
- **Behavior**:
  - Output starts LOW.
  - When `vin` rises above `0.6 V`, output becomes HIGH.
  - When `vin` falls below `0.3 V`, output becomes LOW.
  - Between thresholds, hold the previous state.
  - Drive output with `transition(...)`.

## Constraints

- .., +1))`, `@(cross(..., -1))`, and `@(initial_step)`.
- Pure voltage-domain only.
- No `I() <+`, `ddt()`, or `idt()`.

Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `vin`: input electrical
- `out`: output electrical

## Output Contract (MANDATORY)

- Return exactly two fenced code blocks:
  - first block: Verilog-A DUT (` ```verilog-a ... ``` `)
  - second block: Spectre testbench (` ```spectre ... ``` `)
- The Spectre testbench must include the DUT with `ahdl_include "<module>.va"`.
- Use a single `tran` analysis and include the required `save` signals for checker evaluation.


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=90n maxstep=20p errpreset=conservative
```

Required public waveform columns in `tran.csv`:

- `time`, `vin`, `out`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Public stimulus nodes used by the reference harness include: `VDD`, `VSS`, `vin`.
