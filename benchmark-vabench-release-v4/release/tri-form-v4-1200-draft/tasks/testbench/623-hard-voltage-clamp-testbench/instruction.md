# Hard Voltage Clamp Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Hard Voltage Clamp` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `hard_voltage_clamp_behavior.va`:
  - Module `hard_voltage_clamp_behavior` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `vout` (output, electrical)
    - position 2: `vgnd` (input, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `hard_voltage_clamp_behavior` as `XDUT` with ordered public binding: vin=vin, vout=vout, vgnd=vgnd.

## Public Parameter Contract

- `hard_voltage_clamp_behavior.vclamp_upper` defaults to `1`; valid range: finite; overrides vclamp_upper.
- `hard_voltage_clamp_behavior.vclamp_lower` defaults to `0`; valid range: finite; overrides vclamp_lower.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_GROUND_REFERENCED_INPUT`: exercise and make observable: Measure the clamp input as `V(vin, vgnd)` and drive `V(vout, vgnd)` relative to the same reference. Required traces: `time`, `vin`, `vout`.
- `P_PASSBAND_TRANSFER`: exercise and make observable: When the referenced input lies inside `[vclamp_lower, vclamp_upper]`, pass that referenced voltage to the output. Required traces: `time`, `vin`, `vout`.
- `P_LOWER_CLAMP`: exercise and make observable: When the referenced input is below `vclamp_lower`, drive the lower clamp value. Required traces: `time`, `vin`, `vout`.
- `P_UPPER_CLAMP`: exercise and make observable: When the referenced input is above `vclamp_upper`, drive the upper clamp value. Required traces: `time`, `vin`, `vout`.

The required trace names are: `time`, `vin`, `vout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
