# RF Mixer Downconverter Macro Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `RF Mixer Downconverter Macro` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `rf_mixer_downconverter_macro.va`:
  - Module `rf_mixer_downconverter_macro` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `out` (output, electrical)
    - position 4: `metric` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `rf_mixer_downconverter_macro` as `XDUT` with ordered public binding: clk=clk, rst=rst, vin=vin, out=out, metric=metric.

## Public Parameter Contract

- `rf_mixer_downconverter_macro.tr` defaults to `8e-11` s; valid range: tr > 0; sets smoothing for discontinuous output and metric target changes.
- `rf_mixer_downconverter_macro.vth` defaults to `0.45` V; valid range: 0 < vth < 0.9; sets rst logic threshold and LO polarity decision threshold.
- `rf_mixer_downconverter_macro.conv_gain` defaults to `1.25`; valid range: conv_gain > 0; sets conversion gain applied to the input deviation about 0.45 V.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_COMMON_MODE`: exercise and make observable: Active reset drives out to 0.45 V common mode and metric low. Required traces: `time`, `rst`, `out`, `metric`.
- `P_LO_POLARITY`: exercise and make observable: With reset inactive, clk above vth selects LO coefficient +1 and clk at or below vth selects coefficient -1. Required traces: `time`, `clk`, `rst`, `vin`, `out`.
- `P_DOWNCONVERSION_TRANSFER`: exercise and make observable: The baseband target is 0.45 V plus conv_gain times vin minus 0.45 V times the selected LO coefficient. Required traces: `time`, `clk`, `vin`, `out`.
- `P_ACTIVE_METRIC`: exercise and make observable: Metric is 0.9 V while reset is inactive and conversion is active, and low during reset. Required traces: `time`, `rst`, `metric`.
- `P_OUTPUT_CLAMP`: exercise and make observable: Out is clamped to 0.02 V through 0.88 V and changes with finite smoothing. Required traces: `time`, `out`.

The required trace names are: `time`, `clk`, `rst`, `vin`, `out`, `metric`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
