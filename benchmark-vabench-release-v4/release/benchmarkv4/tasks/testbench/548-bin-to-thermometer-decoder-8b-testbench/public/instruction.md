# Binary To Thermometer Decoder 8b Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Binary To Thermometer Decoder 8b` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `bin_to_therm_8b.va`:
  - Module `bin_to_therm_8b` (entry)
    - position 0: `en` (input, electrical)
    - position 1: `b[7:0]` (input, electrical)
    - position 2: `th[255:0]` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `bin_to_therm_8b` as `XDUT` with ordered public binding: en=en, b[7:0]=b[7:0], th[255:0]=th[255:0].

## Public Parameter Contract

- `bin_to_therm_8b.vdd` defaults to `0.9` V; valid range: vdd > 0; sets the thermometer-bus logic-high voltage.
- `bin_to_therm_8b.vth` defaults to `0.45` V; valid range: 0 < vth < vdd; sets en and binary-input decision thresholds.
- `bin_to_therm_8b.tr` defaults to `2e-11` s; valid range: tr > 0; sets every thermometer output transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_UNSIGNED_CODE`: exercise and make observable: The voltage-coded b[7:0] bus decodes as an unsigned integer from 0 through 255 with b[7] as the most significant bit. Required traces: `time`, `b[7:0]`.
- `P_DISABLED_ALL_LOW`: exercise and make observable: When en is below vth, every th[255:0] output is low independent of the binary code. Required traces: `time`, `en`, `b[7:0]`, `th[255:0]`.
- `P_PREFIX_THERMOMETER`: exercise and make observable: When enabled, exactly code outputs form a contiguous high prefix from th[0] through th[code-1], with all higher indices low. Required traces: `time`, `en`, `b[7:0]`, `th[255:0]`.
- `P_ENDPOINT_CODES`: exercise and make observable: Enabled code 0 drives all outputs low; enabled code 255 drives th[0] through th[254] high and leaves th[255] low. Required traces: `time`, `en`, `b[7:0]`, `th[255:0]`.
- `P_LOGIC_LEVELS`: exercise and make observable: High thermometer elements approach vdd and low elements approach 0 V with finite transition smoothing set by tr. Required traces: `time`, `th[255:0]`.

The required trace names are: `time`, `en`, `b[7:0]`, `th[255:0]`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
