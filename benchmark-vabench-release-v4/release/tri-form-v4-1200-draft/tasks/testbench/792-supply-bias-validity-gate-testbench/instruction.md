# Supply Bias Validity Gate Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Supply Bias Validity Gate` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `supply_bias_validity_gate.va`:
  - Module `supply_bias_validity_gate` (entry)
    - position 0: `vdd` (input, electrical)
    - position 1: `vss` (input, electrical)
    - position 2: `vbias` (input, electrical)
    - position 3: `en` (input, electrical)
    - position 4: `pd` (input, electrical)
    - position 5: `ok` (output, electrical)
    - position 6: `gated` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `supply_bias_validity_gate` as `XDUT` with ordered public binding: vdd=vdd, vss=vss, vbias=vbias, en=en, pd=pd, ok=ok, gated=gated.

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

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_MODEL_A_REUSABLE_SUPPLY_BIAS_VALIDITY`: exercise and make observable: Model a reusable supply/bias validity gate for a behavioral AMS block. Drive `ok` high only when the local supply is inside the supply window, the local ground rail is close enough to the global reference, and the bias input is inside its `vss`-referenced window. Drive `gated` high only when `ok` is high, `en` is high, and `pd` is low. Both outputs must be voltage-coded and smoothed with `transition()`. Required traces: `time`, `en`, `gated`, `ok`, `pd`, `vbias`, `vdd`, `vss`.
- `P_BUILD_A_VOLTAGE_DOMAIN_BIAS_REFERENCE`: exercise and make observable: Build a voltage-domain bias/reference/power-management DUT. The module reports whether local supply, local ground, and local bias conditions are valid, then gates a downstream drive-enable output with public enable and power-down inputs. Required traces: `time`, `en`, `gated`, `ok`, `pd`, `vbias`, `vdd`, `vss`.
- `P_VTH_0_45_V_LOGIC_THRESHOLD`: exercise and make observable: `vth = 0.45 V`: logic threshold for `en` and `pd`. Required traces: `time`, `en`, `gated`, `ok`, `pd`, `vbias`, `vdd`, `vss`.
- `P_VHI_0_9_V_HIGH_LEVEL`: exercise and make observable: `vhi = 0.9 V`: high level for `ok` and `gated`. Required traces: `time`, `en`, `gated`, `ok`, `pd`, `vbias`, `vdd`, `vss`.
- `P_VDD_MIN_0_75_V_VDD`: exercise and make observable: `vdd_min = 0.75 V`, `vdd_max = 1.05 V`: valid supply-voltage window measured Required traces: `time`, `en`, `gated`, `ok`, `pd`, `vbias`, `vdd`, `vss`.
- `P_VSS_MAX_0_08_V_MAXIMUM`: exercise and make observable: `vss_max = 0.08 V`: maximum absolute ground-rail displacement allowed for Required traces: `time`, `en`, `gated`, `ok`, `pd`, `vbias`, `vdd`, `vss`.

The required trace names are: `time`, `en`, `gated`, `ok`, `pd`, `vbias`, `vdd`, `vss`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
