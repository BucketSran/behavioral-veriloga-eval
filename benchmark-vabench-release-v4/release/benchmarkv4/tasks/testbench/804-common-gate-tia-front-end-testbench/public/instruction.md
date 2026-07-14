# Common-gate TIA Front-end Macro Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Common-gate TIA Front-end Macro` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `common_gate_tia_front_end.va`:
  - Module `common_gate_tia_front_end` (entry)
    - position 0: `vin_proxy` (inout, electrical)
    - position 1: `bias` (inout, electrical)
    - position 2: `enable` (inout, electrical)
    - position 3: `rst` (inout, electrical)
    - position 4: `vout` (inout, electrical)
    - position 5: `transimpedance_metric` (inout, electrical)
    - position 6: `overload` (inout, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `common_gate_tia_front_end` as `XDUT` with ordered public binding: vin_proxy=vin_proxy, bias=bias, enable=enable, rst=rst, vout=vout, transimpedance_metric=transimpedance_metric, overload=overload.

## Public Parameter Contract

- `common_gate_tia_front_end.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `common_gate_tia_front_end.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `common_gate_tia_front_end.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `common_gate_tia_front_end.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `common_gate_tia_front_end.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `common_gate_tia_front_end.rz_gain` defaults to `3.0`; valid range: finite; overrides rz_gain.
- `common_gate_tia_front_end.bias_min` defaults to `0.3`; valid range: finite; overrides bias_min.
- `common_gate_tia_front_end.tick` defaults to `500p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_RESET_OR_WHEN_DISABLED_DRIVE`: exercise and make observable: On reset or when disabled, drive `vout` to `vcm` and clear the metrics. Required traces: `time`, `vin_proxy`, `bias`, `enable`, `rst`, `vout`, `transimpedance_metric`, `overload`.
- `P_TREAT_VIN_PROXY_AS_A_VOLTAGE`: exercise and make observable: Treat `vin_proxy` as a voltage-domain proxy for input current magnitude. Required traces: `time`, `vin_proxy`, `bias`, `enable`, `rst`, `vout`, `transimpedance_metric`, `overload`.
- `P_GENERATE_AN_OUTPUT_DEVIATION_AROUND_VCM`: exercise and make observable: Generate an output deviation around `vcm` proportional to the proxy input and `rz_gain`. Required traces: `time`, `vin_proxy`, `bias`, `enable`, `rst`, `vout`, `transimpedance_metric`, `overload`.
- `P_REDUCE_EFFECTIVE_GAIN_WHEN_BIAS_FALLS`: exercise and make observable: Reduce effective gain when `bias` falls below `bias_min` and expose the effective gain on `transimpedance_metric`. Required traces: `time`, `vin_proxy`, `bias`, `enable`, `rst`, `vout`, `transimpedance_metric`, `overload`.
- `P_ASSERT_OVERLOAD_WHEN_THE_UNCLAMPED_OUTPUT`: exercise and make observable: Assert `overload` when the unclamped output target would exceed the rails. Required traces: `time`, `vin_proxy`, `bias`, `enable`, `rst`, `vout`, `transimpedance_metric`, `overload`.
- `P_USE_ONLY_VOLTAGE_DOMAIN_BEHAVIORAL_STATE`: exercise and make observable: Use only voltage-domain behavioral state and voltage contributions on public electrical outputs. Required traces: `time`, `vin_proxy`, `bias`, `enable`, `rst`, `vout`, `transimpedance_metric`, `overload`.

The required trace names are: `time`, `vin_proxy`, `bias`, `enable`, `rst`, `vout`, `transimpedance_metric`, `overload`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
