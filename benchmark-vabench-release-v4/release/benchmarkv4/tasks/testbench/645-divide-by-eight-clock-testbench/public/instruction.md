# Divide By Eight Clock Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Divide By Eight Clock` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `divide_by_eight_clock.va`:
  - Module `divide_by_eight_clock` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `en` (input, electrical)
    - position 3: `vout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `divide_by_eight_clock` as `XDUT` with ordered public binding: vin=vin, rst=rst, en=en, vout=vout.

## Public Parameter Contract

- `divide_by_eight_clock.divisor` defaults to `8`; valid range: finite; overrides divisor.
- `divide_by_eight_clock.tdel` defaults to `10p`; valid range: finite; overrides tdel.
- `divide_by_eight_clock.tr` defaults to `20p`; valid range: finite; overrides tr.
- `divide_by_eight_clock.tf` defaults to `20p`; valid range: finite; overrides tf.
- `divide_by_eight_clock.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `divide_by_eight_clock.vth` defaults to `0.45`; valid range: finite; overrides vth.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_FORCES_INITIAL_HIGH`: exercise and make observable: Active-high `rst` forces the divider counter to zero and drives `vout` high regardless of input-clock activity. Required traces: `time`, `en`, `rst`, `vin`, `vout`.
- `P_ENABLE_QUALIFIED_DIVIDE_BY_EIGHT`: exercise and make observable: Rising `vin` crossings through `vth` advance the divide-by-eight counter only while `en` is high. Required traces: `time`, `en`, `rst`, `vin`, `vout`.
- `P_OUTPUT_DUTY_AND_LEVEL`: exercise and make observable: The divided waveform follows the specified high/low count window and uses the declared high and low voltage levels. Required traces: `time`, `en`, `rst`, `vin`, `vout`.

The required trace names are: `time`, `en`, `rst`, `vin`, `vout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
