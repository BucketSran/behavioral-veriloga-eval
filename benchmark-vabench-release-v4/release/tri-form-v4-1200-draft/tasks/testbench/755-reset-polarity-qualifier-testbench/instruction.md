# Reset Polarity Qualifier Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Reset Polarity Qualifier` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `reset_polarity_qualifier.va`:
  - Module `reset_polarity_qualifier` (entry)
    - position 0: `in0` (input, electrical)
    - position 1: `in1` (input, electrical)
    - position 2: `in2` (input, electrical)
    - position 3: `in3` (input, electrical)
    - position 4: `ctrl0` (input, electrical)
    - position 5: `ctrl1` (input, electrical)
    - position 6: `vdd` (input, electrical)
    - position 7: `vss` (input, electrical)
    - position 8: `en` (input, electrical)
    - position 9: `out` (output, electrical)
    - position 10: `flag` (output, electrical)
    - position 11: `metric` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `reset_polarity_qualifier` as `XDUT` with ordered public binding: in0=in0, in1=in1, in2=in2, in3=in3, ctrl0=ctrl0, ctrl1=ctrl1, vdd=vdd, vss=vss, en=en, out=out, flag=flag, metric=metric.

## Public Parameter Contract

- `reset_polarity_qualifier.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `reset_polarity_qualifier.vhi` defaults to `0.9`; valid range: finite; overrides vhi.
- `reset_polarity_qualifier.span_min` defaults to `0.62`; valid range: finite; overrides span_min.
- `reset_polarity_qualifier.span_max` defaults to `1.28`; valid range: finite; overrides span_max.
- `reset_polarity_qualifier.tr` defaults to `50p`; valid range: finite; overrides tr.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_MEASURE_ANALOG_INPUTS_RELATIVE_TO_THE`: exercise and make observable: Measure analog inputs relative to the local `vss` rail and normalize by the current local supply span. Let `span = V(vdd, vss)` and treat the row as valid only when `V(en) > vth` and `span_min <= span <= span_max`; otherwise drive `out`, `flag`, and `metric` to `0 V`. If `span` is below `0.05 V`, use `0.05 V` as the normalization span. Define `clip01(y)` as `y` limited to the range `[0, 1]`, `x0 = clip01((V(in0) - V(vss)) / span)`, and `c0 = clip01(V(ctrl0) / vhi)`. Required traces: `time`, `ctrl0`, `ctrl1`, `en`, `flag`, `in0`, `in1`, `in2`, `in3`, `metric`, `out`, `vdd`, `vss`.
- `P_DRIVE_OUT_VHI_CLIP01_X0_ASSERT`: exercise and make observable: Drive `out = vhi * clip01(x0)`. Assert `flag = vhi` only when the normalized release level is inside the public window `0.24 <= x0 <= 0.72` and `c0 > 0.35`; otherwise drive `flag = 0 V`. Drive `metric = vhi * clip01(abs(x0 - 0.48) / 0.48)` as the bounded distance from the center of the release window. Required traces: `time`, `ctrl0`, `ctrl1`, `en`, `flag`, `in0`, `in1`, `in2`, `in3`, `metric`, `out`, `vdd`, `vss`.
- `P_BUILD_A_VOLTAGE_DOMAIN_ANALOG_MIXED`: exercise and make observable: Build a voltage-domain analog/mixed-signal helper or monitor. Electrical reset-release qualifier that uses a rail-normalized input window and a voltage-coded control qualifier to produce a release flag inside a valid supply window. Required traces: `time`, `ctrl0`, `ctrl1`, `en`, `flag`, `in0`, `in1`, `in2`, `in3`, `metric`, `out`, `vdd`, `vss`.
- `P_VTH_0_45_V_LOGIC_THRESHOLD`: exercise and make observable: `vth = 0.45 V`: logic threshold for voltage-coded controls. Required traces: `time`, `ctrl0`, `ctrl1`, `en`, `flag`, `in0`, `in1`, `in2`, `in3`, `metric`, `out`, `vdd`, `vss`.
- `P_VHI_0_9_V_HIGH_LEVEL`: exercise and make observable: `vhi = 0.9 V`: high level for output observables. Required traces: `time`, `ctrl0`, `ctrl1`, `en`, `flag`, `in0`, `in1`, `in2`, `in3`, `metric`, `out`, `vdd`, `vss`.
- `P_SPAN_MIN_0_62_V_SPAN`: exercise and make observable: `span_min = 0.62 V`, `span_max = 1.28 V`: legal local supply span measured as Required traces: `time`, `ctrl0`, `ctrl1`, `en`, `flag`, `in0`, `in1`, `in2`, `in3`, `metric`, `out`, `vdd`, `vss`.

The required trace names are: `time`, `ctrl0`, `ctrl1`, `en`, `flag`, `in0`, `in1`, `in2`, `in3`, `metric`, `out`, `vdd`, `vss`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
