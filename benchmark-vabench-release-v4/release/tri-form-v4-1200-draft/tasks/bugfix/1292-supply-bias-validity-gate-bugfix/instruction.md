# Supply Bias Validity Gate Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `supply_bias_validity_gate.va`:
  - Module `supply_bias_validity_gate` (entry)
    - position 0: `vdd` (input, electrical)
    - position 1: `vss` (input, electrical)
    - position 2: `vbias` (input, electrical)
    - position 3: `en` (input, electrical)
    - position 4: `pd` (input, electrical)
    - position 5: `ok` (output, electrical)
    - position 6: `gated` (output, electrical)

## Public Parameter Contract

- `supply_bias_validity_gate.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `supply_bias_validity_gate.vhi` defaults to `0.9`; valid range: finite; overrides vhi.
- `supply_bias_validity_gate.vdd_min` defaults to `0.75`; valid range: finite; overrides vdd_min.
- `supply_bias_validity_gate.vdd_max` defaults to `1.05`; valid range: finite; overrides vdd_max.
- `supply_bias_validity_gate.vss_max` defaults to `0.08`; valid range: finite; overrides vss_max.
- `supply_bias_validity_gate.vbias_min` defaults to `0.25`; valid range: finite; overrides vbias_min.
- `supply_bias_validity_gate.vbias_max` defaults to `0.75`; valid range: finite; overrides vbias_max.
- `supply_bias_validity_gate.tr` defaults to `50p`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_MODEL_A_REUSABLE_SUPPLY_BIAS_VALIDITY`: restore: Model a reusable supply/bias validity gate for a behavioral AMS block. Drive `ok` high only when the local supply is inside the supply window, the local ground rail is close enough to the global reference, and the bias input is inside its `vss`-referenced window. Drive `gated` high only when `ok` is high, `en` is high, and `pd` is low. Both outputs must be voltage-coded and smoothed with `transition()`. Required traces: `time`, `en`, `gated`, `ok`, `pd`, `vbias`, `vdd`, `vss`.
- `P_BUILD_A_VOLTAGE_DOMAIN_BIAS_REFERENCE`: restore: Build a voltage-domain bias/reference/power-management DUT. The module reports whether local supply, local ground, and local bias conditions are valid, then gates a downstream drive-enable output with public enable and power-down inputs. Required traces: `time`, `en`, `gated`, `ok`, `pd`, `vbias`, `vdd`, `vss`.
- `P_VTH_0_45_V_LOGIC_THRESHOLD`: restore: `vth = 0.45 V`: logic threshold for `en` and `pd`. Required traces: `time`, `en`, `gated`, `ok`, `pd`, `vbias`, `vdd`, `vss`.
- `P_VHI_0_9_V_HIGH_LEVEL`: restore: `vhi = 0.9 V`: high level for `ok` and `gated`. Required traces: `time`, `en`, `gated`, `ok`, `pd`, `vbias`, `vdd`, `vss`.
- `P_VDD_MIN_0_75_V_VDD`: restore: `vdd_min = 0.75 V`, `vdd_max = 1.05 V`: valid supply-voltage window measured Required traces: `time`, `en`, `gated`, `ok`, `pd`, `vbias`, `vdd`, `vss`.
- `P_VSS_MAX_0_08_V_MAXIMUM`: restore: `vss_max = 0.08 V`: maximum absolute ground-rail displacement allowed for Required traces: `time`, `en`, `gated`, `ok`, `pd`, `vbias`, `vdd`, `vss`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `supply_bias_validity_gate.va`.
Every supplied `.va` file is editable; do not add or omit files.
