# Gain Trim Controller Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Gain Trim Controller` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `gain_trim_controller.va`:
  - Module `gain_trim_controller` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `meas` (input, electrical)
    - position 3: `target` (input, electrical)
    - position 4: `gain_ctrl` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `gain_trim_controller` as `XDUT` with ordered public binding: clk=clk, rst=rst, meas=meas, target=target, gain_ctrl=gain_ctrl.

## Public Parameter Contract

- `gain_trim_controller.vth` defaults to `0.45` V; valid range: vth > 0; sets clk and rst decision threshold.
- `gain_trim_controller.tr` defaults to `5e-10` s; valid range: tr > 0; sets gain_ctrl transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_INITIAL_AND_RESET`: exercise and make observable: gain_ctrl initializes to 0.30 V and returns to 0.30 V on a rising clk edge while rst is high. Required traces: `time`, `clk`, `rst`, `gain_ctrl`.
- `P_ERROR_DIRECTION`: exercise and make observable: On rising clk edges, gain_ctrl increases by 0.05 V below target-0.02 V and decreases by 0.05 V above target+0.02 V. Required traces: `time`, `clk`, `rst`, `meas`, `target`, `gain_ctrl`.
- `P_DEADBAND_HOLD`: exercise and make observable: gain_ctrl holds when meas is within the inclusive target deadband. Required traces: `time`, `clk`, `meas`, `target`, `gain_ctrl`.
- `P_CONTROL_CLAMP`: exercise and make observable: gain_ctrl remains within the inclusive 0.05 V to 0.85 V range. Required traces: `time`, `gain_ctrl`.

The required trace names are: `time`, `clk`, `rst`, `meas`, `target`, `gain_ctrl`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
