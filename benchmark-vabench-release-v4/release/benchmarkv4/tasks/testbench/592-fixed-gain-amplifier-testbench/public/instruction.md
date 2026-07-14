# Fixed Gain Amplifier Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Fixed Gain Amplifier` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `gain_amp_fixed.va`:
  - Module `gain_amp_fixed` (entry)
    - position 0: `VIN_P` (input, electrical)
    - position 1: `VIN_N` (input, electrical)
    - position 2: `VOUT_P` (output, electrical)
    - position 3: `VOUT_N` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `gain_amp_fixed` as `XDUT` with ordered public binding: VIN_P=vin_p, VIN_N=vin_n, VOUT_P=vout_p, VOUT_N=vout_n.

## Public Parameter Contract

- `gain_amp_fixed.vdd` defaults to `0.9` V; valid range: vdd > 0; sets twice the output common-mode level.
- `gain_amp_fixed.ACTUAL_GAIN` defaults to `8.64` V/V; valid range: ACTUAL_GAIN > 0; sets positive differential voltage gain.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_DIFFERENTIAL_GAIN`: exercise and make observable: The output differential equals ACTUAL_GAIN times the input differential. Required traces: `time`, `vin_p`, `vin_n`, `vout_p`, `vout_n`.
- `P_POSITIVE_POLARITY`: exercise and make observable: A positive input differential produces a positive output differential and a negative input differential produces a negative output differential. Required traces: `time`, `vin_p`, `vin_n`, `vout_p`, `vout_n`.
- `P_OUTPUT_COMMON_MODE`: exercise and make observable: The output pair remains centered at vdd/2 independently of input common mode. Required traces: `time`, `vin_p`, `vin_n`, `vout_p`, `vout_n`.
- `P_SYMMETRIC_OUTPUT_PAIR`: exercise and make observable: Half the amplified differential is added to VOUT_P and half is subtracted from VOUT_N. Required traces: `time`, `vin_p`, `vin_n`, `vout_p`, `vout_n`.
- `P_PARAMETER_OVERRIDES`: exercise and make observable: Legal ACTUAL_GAIN and vdd overrides alter differential gain and output common mode according to their declared meanings. Required traces: `time`, `vin_p`, `vin_n`, `vout_p`, `vout_n`.

The required trace names are: `time`, `vin_p`, `vin_n`, `vout_p`, `vout_n`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
