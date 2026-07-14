# Ideal Clkmux 8channel Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Ideal Clkmux 8channel` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `ideal_clkmux_8channel.va`:
  - Module `ideal_clkmux_8channel` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `in0` (input, electrical)
    - position 2: `in1` (input, electrical)
    - position 3: `in2` (input, electrical)
    - position 4: `in3` (input, electrical)
    - position 5: `in4` (input, electrical)
    - position 6: `in5` (input, electrical)
    - position 7: `in6` (input, electrical)
    - position 8: `in7` (input, electrical)
    - position 9: `out` (output, electrical)
    - position 10: `count_x` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `ideal_clkmux_8channel` as `XDUT` with ordered public binding: clk=clk, in0=in0, in1=in1, in2=in2, in3=in3, in4=in4, in5=in5, in6=in6, in7=in7, out=out, count_x=count_x.

## Public Parameter Contract

- No public parameter is declared.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_MODULO8_COUNTER`: exercise and make observable: The internal selector starts at zero and increments modulo eight on each rising `clk` crossing through 0.5 V. Required traces: `time`, `clk`, `count_x`.
- `P_INCREMENT_BEFORE_SELECTION`: exercise and make observable: The first qualifying clock event selects the incremented counter state rather than the reset state. Required traces: `time`, `clk`, `count_x`, `out`.
- `P_ANALOG_CHANNEL_MUX`: exercise and make observable: `out` follows the input channel selected by the current counter value. Required traces: `time`, `clk`, `out`, `in0`, `in1`, `in2`, `in3`, `in4`, `in5`, `in6`, `in7`.
- `P_COUNTER_MONITOR_LEVEL`: exercise and make observable: `count_x` reports the current selector count with the specified voltage scaling. Required traces: `time`, `clk`, `count_x`.

The required trace names are: `time`, `clk`, `out`, `count_x`, `in0`, `in1`, `in2`, `in3`, `in4`, `in5`, `in6`, `in7`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
