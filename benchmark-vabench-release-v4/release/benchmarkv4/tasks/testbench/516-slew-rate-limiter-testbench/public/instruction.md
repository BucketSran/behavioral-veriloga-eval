# Slew Rate Limiter Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Slew Rate Limiter` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `slew_rate_limiter.va`:
  - Module `slew_rate_limiter` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `vout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `slew_rate_limiter` as `XDUT` with ordered public binding: vin=vin, vout=vout.

## Public Parameter Contract

- `slew_rate_limiter.step` defaults to `0.015` V; valid range: step > 0; sets maximum state change per update.
- `slew_rate_limiter.tr` defaults to `2e-10` s; valid range: tr > 0; sets output transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_INITIAL_ZERO`: exercise and make observable: vout begins at 0 V. Required traces: `time`, `vout`.
- `P_PERIODIC_UPDATE`: exercise and make observable: The state changes only on the public 1 ns periodic update schedule. Required traces: `time`, `vin`, `vout`.
- `P_BIDIRECTIONAL_STEP_LIMIT`: exercise and make observable: Each rising or falling update changes the state toward vin by no more than step. Required traces: `time`, `vin`, `vout`.
- `P_NEAR_TARGET_SETTLE`: exercise and make observable: When vin is within one step, vout may settle directly to vin. Required traces: `time`, `vin`, `vout`.
- `P_EVENTUAL_TRACKING`: exercise and make observable: The limited response eventually reaches sustained high and low input levels while remaining non-instantaneous. Required traces: `time`, `vin`, `vout`.

The required trace names are: `time`, `vin`, `vout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
