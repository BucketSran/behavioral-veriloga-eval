# Voltage Controlled Gain Amplifier Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Voltage Controlled Gain Amplifier` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `voltage_controlled_gain_amplifier.va`:
  - Module `voltage_controlled_gain_amplifier` (entry)
    - position 0: `vin_p` (input, electrical)
    - position 1: `vin_n` (input, electrical)
    - position 2: `vctrl_p` (input, electrical)
    - position 3: `vctrl_n` (input, electrical)
    - position 4: `vout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `voltage_controlled_gain_amplifier` as `XDUT` with ordered public binding: vin_p=vin_p, vin_n=vin_n, vctrl_p=vctrl_p, vctrl_n=vctrl_n, vout=vout.

## Public Parameter Contract

- No public parameter is declared.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_DIFFERENTIAL_CONTROL`: exercise and make observable: Use `V(vctrl_p, vctrl_n)` as the gain-control voltage. Required traces: `time`, `vctrl_p`, `vctrl_n`, `vout`.
- `P_INPUT_OFFSET_AND_GAIN`: exercise and make observable: Compute the unclamped target as `1.5 * V(vctrl_p, vctrl_n) * (V(vin_p, vin_n) - 0.05) + 0.5`. Required traces: `time`, `vin_p`, `vin_n`, `vctrl_p`, `vctrl_n`, `vout`.
- `P_UNIPOLAR_OUTPUT_CLAMP`: exercise and make observable: Clamp the final output target to the inclusive interval `[0.1 V, 0.9 V]`. Required traces: `time`, `vout`.

The required trace names are: `time`, `vctrl_n`, `vctrl_p`, `vin_n`, `vin_p`, `vout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
