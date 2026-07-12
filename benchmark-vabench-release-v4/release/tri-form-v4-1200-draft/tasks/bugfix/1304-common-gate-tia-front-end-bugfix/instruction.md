# Common-gate TIA Front-end Macro Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `common_gate_tia_front_end.va`:
  - Module `common_gate_tia_front_end` (entry)
    - position 0: `vin_proxy` (inout, electrical)
    - position 1: `bias` (inout, electrical)
    - position 2: `enable` (inout, electrical)
    - position 3: `rst` (inout, electrical)
    - position 4: `vout` (inout, electrical)
    - position 5: `transimpedance_metric` (inout, electrical)
    - position 6: `overload` (inout, electrical)

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

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_DISABLED_DRIVE`: restore: On reset or when disabled, drive `vout` to `vcm` and clear the metrics. Required traces: `time`, `vin_proxy`, `bias`, `enable`, `rst`, `vout`, `transimpedance_metric`, `overload`.
- `P_TREAT_VIN_PROXY_AS_A_VOLTAGE`: restore: Treat `vin_proxy` as a voltage-domain proxy for input current magnitude. Required traces: `time`, `vin_proxy`, `bias`, `enable`, `rst`, `vout`, `transimpedance_metric`, `overload`.
- `P_GENERATE_AN_OUTPUT_DEVIATION_AROUND_VCM`: restore: Generate an output deviation around `vcm` proportional to the proxy input and `rz_gain`. Required traces: `time`, `vin_proxy`, `bias`, `enable`, `rst`, `vout`, `transimpedance_metric`, `overload`.
- `P_REDUCE_EFFECTIVE_GAIN_WHEN_BIAS_FALLS`: restore: Reduce effective gain when `bias` falls below `bias_min` and expose the effective gain on `transimpedance_metric`. Required traces: `time`, `vin_proxy`, `bias`, `enable`, `rst`, `vout`, `transimpedance_metric`, `overload`.
- `P_ASSERT_OVERLOAD_WHEN_THE_UNCLAMPED_OUTPUT`: restore: Assert `overload` when the unclamped output target would exceed the rails. Required traces: `time`, `vin_proxy`, `bias`, `enable`, `rst`, `vout`, `transimpedance_metric`, `overload`.
- `P_USE_ONLY_VOLTAGE_DOMAIN_BEHAVIORAL_STATE`: restore: Use only voltage-domain behavioral state and voltage contributions on public electrical outputs. Required traces: `time`, `vin_proxy`, `bias`, `enable`, `rst`, `vout`, `transimpedance_metric`, `overload`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `common_gate_tia_front_end.va`.
Every supplied `.va` file is editable; do not add or omit files.
