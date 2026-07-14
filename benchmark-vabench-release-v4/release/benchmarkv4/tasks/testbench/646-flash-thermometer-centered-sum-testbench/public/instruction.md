# Flash Thermometer Centered Sum Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Flash Thermometer Centered Sum` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `flash_thermometer_centered_sum.va`:
  - Module `flash_thermometer_centered_sum` (entry)
    - position 0: `b0` (input, electrical)
    - position 1: `b1` (input, electrical)
    - position 2: `b2` (input, electrical)
    - position 3: `b3` (input, electrical)
    - position 4: `b4` (input, electrical)
    - position 5: `b5` (input, electrical)
    - position 6: `b6` (input, electrical)
    - position 7: `b7` (input, electrical)
    - position 8: `dout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `flash_thermometer_centered_sum` as `XDUT` with ordered public binding: b0=b0, b1=b1, b2=b2, b3=b3, b4=b4, b5=b5, b6=b6, b7=b7, dout=dout.

## Public Parameter Contract

- `flash_thermometer_centered_sum.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `flash_thermometer_centered_sum.gain` defaults to `0.1125`; valid range: finite; overrides gain.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_THERMOMETER_THRESHOLD_COUNT`: exercise and make observable: Each `b0` through `b7` input above `vth` contributes exactly one count to the thermometer total. Required traces: `time`, `b0`, `b1`, `b2`, `b3`, `b4`, `b5`, `b6`, `b7`, `dout`.
- `P_CENTERED_SUM`: exercise and make observable: The output subtracts the four-count midpoint so the analog sum is centered around zero asserted-input balance. Required traces: `time`, `b0`, `b1`, `b2`, `b3`, `b4`, `b5`, `b6`, `b7`, `dout`.
- `P_OUTPUT_GAIN`: exercise and make observable: The centered count is multiplied by `gain` and driven on `dout` without extra scaling. Required traces: `time`, `b0`, `b1`, `b2`, `b3`, `b4`, `b5`, `b6`, `b7`, `dout`.

The required trace names are: `time`, `b0`, `b1`, `b2`, `b3`, `b4`, `b5`, `b6`, `b7`, `dout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
