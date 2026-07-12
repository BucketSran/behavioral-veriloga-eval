# Analog Mux Threshold Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Analog Mux Threshold` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `analog_mux_threshold.va`:
  - Module `analog_mux_threshold` (entry)
    - position 0: `vin1` (input, electrical)
    - position 1: `vin2` (input, electrical)
    - position 2: `vsel` (input, electrical)
    - position 3: `vout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `analog_mux_threshold` as `XDUT` with ordered public binding: vin1=vin1, vin2=vin2, vsel=vsel, vout=vout.

## Public Parameter Contract

- `analog_mux_threshold.vth` defaults to `0.45` V; valid range: finite real value; sets the select threshold used for initial selection and subsequent threshold crossings.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_HIGH_SELECTS_VIN1`: exercise and make observable: When vsel is above vth, vout follows vin1 rather than vin2. Required traces: `time`, `vin1`, `vin2`, `vsel`, `vout`.
- `P_LOW_SELECTS_VIN2`: exercise and make observable: When vsel is at or below vth, vout follows vin2 rather than vin1. Required traces: `time`, `vin1`, `vin2`, `vsel`, `vout`.
- `P_BIDIRECTIONAL_SELECTION`: exercise and make observable: The selected input updates after both rising and falling crossings of vsel through vth. Required traces: `time`, `vin1`, `vin2`, `vsel`, `vout`.
- `P_INITIAL_SELECTION`: exercise and make observable: Before any select transition, vout is selected from the initial vsel level using the same strict-greater-than threshold rule. Required traces: `time`, `vin1`, `vin2`, `vsel`, `vout`.
- `P_NO_MIXING`: exercise and make observable: The output represents one selected input and does not average or sum vin1 and vin2. Required traces: `time`, `vin1`, `vin2`, `vsel`, `vout`.

The required trace names are: `time`, `vin1`, `vin2`, `vsel`, `vout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
