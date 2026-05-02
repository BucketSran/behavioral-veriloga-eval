Write a Verilog-A module named `adjacent_code_counter`.

# Task: gray_counter_4b_p1p2

## Objective

Create a 4-bit counter behavioral model in Verilog-A where consecutive output
values differ by exactly one bit, and a minimal EVAS-compatible Spectre testbench.

## Specification

- **Module name**: `adjacent_code_counter`
- **Ports** (all `electrical`, exactly as named):
  `supply_hi`, `supply_lo`, `strobe`, `enable`, `reset_n`, `qb3`, `qb2`, `qb1`, `qb0`
- **Parameters**: `vth` (real, default 0.45), `tedge` (real, default 100p)
- **Behavior**:
  - On each rising `strobe` edge, if `enable` is high and `reset_n` is high,
    increment an internal counter (mod 16).
  - Map the internal count to a 4-bit code where **each increment changes only
    one output bit**.
  - Drive `qb3` (MSB), `qb2`, `qb1`, `qb0` (LSB) with the encoded outputs.
  - `reset_n` low (active-low reset) resets the counter to 0.
- **Output**: use `transition()` only. No `idt` or current domain.

## Testbench requirements

Create a minimal Spectre testbench that:
- Includes `adjacent_code_counter.va` via `ahdl_include`
- Provides supply_hi=0.9V, supply_lo=0V
- Generates strobe and enable signals
- Saves signals: `strobe`, `reset_n`, `qb3`, `qb2`, `qb1`, `qb0`
- Runs transient for ~2us (at least 16 strobe cycles)

## Deliverable

Two files:
1. `adjacent_code_counter.va` - the Verilog-A behavioral model
2. `tb_adjacent_code_counter.scs` - the Spectre testbench

Expected behavior:
- Only ONE bit should change between consecutive states
- Code sequence: 0000→0001→0011→0010→0110→0111→0101→0100→1100→...
- Counter should wrap around correctly

Ports:
- `SUPPLY_HI`: inout electrical
- `SUPPLY_LO`: inout electrical
- `STROBE`: input electrical
- `ENABLE`: input electrical
- `RESET_N`: input electrical
- `QB3`: output electrical
- `QB2`: output electrical
- `QB1`: output electrical
- `QB0`: output electrical

## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the
generated artifact. It does not prescribe the internal implementation or reveal
a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=2u maxstep=500p errpreset=conservative
```

Required public waveform columns in `tran.csv`:

- `strobe`, `reset_n`, `qb3`, `qb2`, `qb1`, `qb0`

Use plain scalar save names for these observables; do not rely on
instance-qualified or aliased save names.

Timing/checking-window contract:

- Reset-like input(s) `reset_n` must be asserted only for startup/explicit reset
  checks, then deasserted early enough and kept deasserted through the post-reset
  checking window.
- For active-low resets such as `reset_n`, avoid a finite-width pulse that
  returns the reset node low after release; use a waveform that remains high
  during checking.
- Enable-like input(s) `enable` must be in the enabled state during the
  post-reset checking window unless the task explicitly asks for disabled intervals.
- The `strobe` input must provide enough valid edges after reset/enable for the
  checker to sample settled outputs.
- Sequential outputs are sampled shortly after strobe edges, so drive outputs
  with stable held state variables and `transition()` targets.
- Public stimulus nodes used by the reference harness include: `supply_hi`,
  `supply_lo`, `enable`, `reset_n`, `strobe`.
