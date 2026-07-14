# Reference Step Clock Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Reference Step Clock` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `ref_step_clk.va`:
  - Module `ref_step_clk` (entry)
    - position 0: `VDD` (inout, electrical)
    - position 1: `VSS` (inout, electrical)
    - position 2: `CLK` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `ref_step_clk` as `XDUT` with ordered public binding: VDD=vdd, VSS=vss, CLK=clk.

## Public Parameter Contract

- `ref_step_clk.period_pre` defaults to `2e-08` s; valid range: period_pre > 0; sets the full clock period before t_switch.
- `ref_step_clk.period_post` defaults to `1.95e-08` s; valid range: period_post > 0; sets the full clock period for cycles scheduled after t_switch.
- `ref_step_clk.t_switch` defaults to `2e-06` s; valid range: t_switch >= 0; sets the cadence-change boundary.
- `ref_step_clk.tedge` defaults to `1e-10` s; valid range: tedge > 0; sets CLK rise and fall smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_SUPPLY_REFERENCED_RAILS`: exercise and make observable: CLK low and high levels track VSS and VDD respectively. Required traces: `time`, `VDD`, `VSS`, `CLK`.
- `P_PRE_SWITCH_PERIOD`: exercise and make observable: Clock cycles before t_switch have full period period_pre. Required traces: `time`, `CLK`.
- `P_POST_SWITCH_PERIOD`: exercise and make observable: Clock cycles scheduled after t_switch have full period period_post. Required traces: `time`, `CLK`.
- `P_CADENCE_STEP`: exercise and make observable: The waveform changes cadence near t_switch without stopping, duplicating, or losing clock transitions. Required traces: `time`, `CLK`.
- `P_HALF_DUTY_CYCLE`: exercise and make observable: CLK duty cycle remains close to 50 percent on both sides of the cadence step. Required traces: `time`, `CLK`.
- `P_PARAMETERIZED_TIMING`: exercise and make observable: Nearby legal overrides of period_pre, period_post, t_switch, and tedge produce the corresponding periods, switch boundary, and edge smoothing. Required traces: `time`, `VDD`, `VSS`, `CLK`.

The required trace names are: `time`, `VDD`, `VSS`, `CLK`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
