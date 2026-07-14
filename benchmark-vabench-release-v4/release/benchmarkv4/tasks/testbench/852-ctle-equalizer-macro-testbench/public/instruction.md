# CTLE Equalizer Macro Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `CTLE Equalizer Macro` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `ctle_equalizer.va`:
  - Module `ctle_equalizer` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `clk` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `boost_2` (input, electrical)
    - position 4: `boost_1` (input, electrical)
    - position 5: `boost_0` (input, electrical)
    - position 6: `vout` (output, electrical)
    - position 7: `edge_metric` (output, electrical)
    - position 8: `sat_flag` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `ctle_equalizer` as `XDUT` with ordered public binding: vin=vin, clk=clk, rst=rst, boost_2=boost_2, boost_1=boost_1, boost_0=boost_0, vout=vout, edge_metric=edge_metric, sat_flag=sat_flag.

## Public Parameter Contract

- `ctle_equalizer.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `ctle_equalizer.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `ctle_equalizer.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `ctle_equalizer.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `ctle_equalizer.base_gain` defaults to `1.0`; valid range: finite; overrides base_gain.
- `ctle_equalizer.boost_step` defaults to `0.08`; valid range: finite; overrides boost_step.
- `ctle_equalizer.tr` defaults to `120p from (0:inf)`; valid range: finite; overrides tr.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_INITIALIZES_THE_EQUALIZED_OUTPUT_TO`: exercise and make observable: Reset initializes the equalized output to common mode and clears metric outputs. Required traces: `time`, `vin`, `clk`, `rst`, `boost_2`, `boost_1`, `boost_0`, `vout`, `edge_metric`, `sat_flag`.
- `P_ON_EACH_RISING_CLK_SAMPLE_THE`: exercise and make observable: On each rising `clk`, sample the boost code and the current input. Required traces: `time`, `vin`, `clk`, `rst`, `boost_2`, `boost_1`, `boost_0`, `vout`, `edge_metric`, `sat_flag`.
- `P_DRIVE_VOUT_FROM_THE_CURRENT_INPUT`: exercise and make observable: Drive `vout` from the current input plus a boost-code-scaled edge term relative to the previous sampled input. Required traces: `time`, `vin`, `clk`, `rst`, `boost_2`, `boost_1`, `boost_0`, `vout`, `edge_metric`, `sat_flag`.
- `P_CLAMP_VOUT_TO_THE_VSS_TO`: exercise and make observable: Clamp `vout` to the `vss` to `vdd` range. Required traces: `time`, `vin`, `clk`, `rst`, `boost_2`, `boost_1`, `boost_0`, `vout`, `edge_metric`, `sat_flag`.
- `P_EDGE_METRIC_REPORTS_THE_ABSOLUTE_BOOSTED`: exercise and make observable: `edge_metric` reports the absolute boosted edge contribution after clipping to full scale. Required traces: `time`, `vin`, `clk`, `rst`, `boost_2`, `boost_1`, `boost_0`, `vout`, `edge_metric`, `sat_flag`.
- `P_SAT_FLAG_IS_HIGH_WHEN_THE`: exercise and make observable: `sat_flag` is high when the unclamped equalized target would exceed either output rail. Required traces: `time`, `vin`, `clk`, `rst`, `boost_2`, `boost_1`, `boost_0`, `vout`, `edge_metric`, `sat_flag`.

The required trace names are: `time`, `vin`, `clk`, `rst`, `boost_2`, `boost_1`, `boost_0`, `vout`, `edge_metric`, `sat_flag`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
