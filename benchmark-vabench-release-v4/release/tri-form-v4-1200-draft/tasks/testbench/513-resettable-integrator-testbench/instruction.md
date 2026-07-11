# Resettable Integrator Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Resettable Integrator` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `resettable_integrator.va`:
  - Module `resettable_integrator` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `resettable_integrator` as `XDUT` with ordered public binding: vin=vin, rst=rst, vout=vout.

## Public Parameter Contract

- `resettable_integrator.vth` defaults to `0.45` V; valid range: vth > 0; sets active-high reset threshold.
- `resettable_integrator.gain` defaults to `1000000000.0` 1/s; valid range: gain >= 0; sets accumulation gain per input volt.
- `resettable_integrator.dt` defaults to `1e-09` s; valid range: dt > 0; sets periodic state update interval.
- `resettable_integrator.vmax` defaults to `0.85` V; valid range: vmax >= 0; sets accumulator upper clamp.
- `resettable_integrator.tr` defaults to `5e-10` s; valid range: tr > 0; sets output transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_INITIAL_ZERO`: exercise and make observable: vout begins at 0 V. Required traces: `time`, `vout`.
- `P_TIMER_INTEGRATION`: exercise and make observable: While reset is low, each dt timer event adds gain*vin*dt to the accumulator. Required traces: `time`, `vin`, `rst`, `vout`.
- `P_ACTIVE_HIGH_RESET`: exercise and make observable: When rst is above vth at a timer event, the accumulator and vout return toward 0 V and later restart from zero. Required traces: `time`, `vin`, `rst`, `vout`.
- `P_ACCUMULATOR_CLAMP`: exercise and make observable: vout remains in the closed 0 V to vmax range. Required traces: `time`, `vout`.
- `P_EVENT_HOLD`: exercise and make observable: The accumulated state changes only on dt timer events. Required traces: `time`, `vin`, `rst`, `vout`.

The required trace names are: `time`, `vin`, `rst`, `vout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
