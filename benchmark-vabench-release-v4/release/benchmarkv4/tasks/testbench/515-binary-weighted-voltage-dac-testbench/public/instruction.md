# Binary Weighted Voltage DAC Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Binary Weighted Voltage DAC` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `simple_binary_voltage_dac_4b.va`:
  - Module `simple_binary_voltage_dac_4b` (entry)
    - position 0: `code_0` (input, electrical)
    - position 1: `code_1` (input, electrical)
    - position 2: `code_2` (input, electrical)
    - position 3: `code_3` (input, electrical)
    - position 4: `vref` (input, electrical)
    - position 5: `vss` (input, electrical)
    - position 6: `aout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `simple_binary_voltage_dac_4b` as `XDUT` with ordered public binding: code_0=code_0, code_1=code_1, code_2=code_2, code_3=code_3, vref=vref, vss=vss, aout=aout.

## Public Parameter Contract

- `simple_binary_voltage_dac_4b.vth` defaults to `0.45` V; valid range: vth > 0; sets code-bit decision threshold.
- `simple_binary_voltage_dac_4b.tr` defaults to `5e-10` s; valid range: tr > 0; sets output transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_BINARY_WEIGHTS`: exercise and make observable: code_0 through code_3 form an unsigned four-bit word with weights one, two, four, and eight. Required traces: `time`, `code_0`, `code_1`, `code_2`, `code_3`, `aout`.
- `P_ENDPOINTS`: exercise and make observable: Code zero maps to vss and code fifteen maps to vref. Required traces: `time`, `code_0`, `code_1`, `code_2`, `code_3`, `vref`, `vss`, `aout`.
- `P_LINEAR_MONOTONIC_MAPPING`: exercise and make observable: aout changes linearly and monotonically with the unsigned code between the rail endpoints. Required traces: `time`, `code_0`, `code_1`, `code_2`, `code_3`, `vref`, `vss`, `aout`.
- `P_CONTINUOUS_UPDATE`: exercise and make observable: aout responds continuously to code-bit changes without a clock event. Required traces: `time`, `code_0`, `code_1`, `code_2`, `code_3`, `aout`.

The required trace names are: `time`, `code_0`, `code_1`, `code_2`, `code_3`, `vref`, `vss`, `aout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
