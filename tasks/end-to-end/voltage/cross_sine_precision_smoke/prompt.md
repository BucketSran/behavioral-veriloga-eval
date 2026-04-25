Write a Verilog-A module named `cross_sine_precision_ref`.

# Task: cross_sine_precision_smoke

## Objective

Write a Verilog-A cross-event precision probe that measures `$abstime` accuracy on a nonlinear sine input.

**Target precision**: The cross event timing must achieve `max_err_ps < 1.0 ps` (i.e., sub-picosecond accuracy). The testbench uses `maxstep=1p` to ensure both EVAS and Spectre can achieve this precision.

## Specification

- **Module name**: `cross_sine_precision_ref`
- **Ports**: `VDD`, `VSS`, `vin`, `first_err_out`, `max_err_out`, `count_out` - all `electrical`
- **Behavior**:
  - Monitor rising `cross(V(vin,VSS)-vth,+1)` events.
  - The testbench drives `vin = 0.45 V + 0.40 V * sin(2*pi*73 MHz*t)`.
  - Since `vth = 0.45 V`, rising crossings after initialization occur at `1/fin`, `2/fin`, and `3/fin`.
  - On each rising crossing, compare `$abstime` against `count/fin` and update the maximum absolute timing error in ps.
  - Drive `first_err_out = VDD * first_abs_err_ps / 10`.
  - Drive `max_err_out = VDD * max_abs_err_ps / 10`.
  - Drive `count_out = VDD * count / 3`.

**Verification criterion**: `max_err_ps < 1.0 ps` (checker passes when timing error is sub-ps).

## Constraints

- Use plain `@(cross(...,+1))` and `$abstime` inside the event body.
- ..)` for outputs.
- Pure voltage-domain only.
- No `time_tol` / `expr_tol` in `cross()`.
- No `I() <+`, `ddt()`, `idt()`, `idtmod()`, or matrix/current-domain constructs.

Expected behavior:
- @(cross()) event should detect zero-crossing precisely
- Timing accuracy within simulation timestep
Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `vin`: input electrical
- `first_err_out`: output electrical
- `max_err_out`: output electrical
- `count_out`: output electrical

Write EVAS-compatible Verilog-A (pure voltage-domain behavioral model, no current contributions).


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=47n maxstep=1p errpreset=conservative
```

Required public waveform columns in `tran.csv`:

- `first_err_out`, `max_err_out`, `count_out`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Public stimulus nodes used by the reference harness include: `VDD`, `VSS`, `vin`.
