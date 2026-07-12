# Configurable Pulse Train Generator Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Configurable Pulse Train Generator` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `configurable_pulse_train.va`:
  - Module `configurable_pulse_train` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `start` (input, electrical)
    - position 2: `period0` (input, electrical)
    - position 3: `period1` (input, electrical)
    - position 4: `period2` (input, electrical)
    - position 5: `period3` (input, electrical)
    - position 6: `width0` (input, electrical)
    - position 7: `width1` (input, electrical)
    - position 8: `width2` (input, electrical)
    - position 9: `width3` (input, electrical)
    - position 10: `count0` (input, electrical)
    - position 11: `count1` (input, electrical)
    - position 12: `count2` (input, electrical)
    - position 13: `count3` (input, electrical)
    - position 14: `pulse` (output, electrical)
    - position 15: `done` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `configurable_pulse_train` as `XDUT` with ordered public binding: clk=clk, start=start, period0=period0, period1=period1, period2=period2, period3=period3, width0=width0, width1=width1, width2=width2, width3=width3, count0=count0, count1=count1, count2=count2, count3=count3, pulse=pulse, done=done.

## Public Parameter Contract

- `configurable_pulse_train.vdd` defaults to `0.9` V; valid range: vdd > 0; sets pulse and done high levels.
- `configurable_pulse_train.vth` defaults to `0.45` V; valid range: 0 < vth < vdd; sets the threshold for clk, start, and every control-word bit.
- `configurable_pulse_train.tr` defaults to `2e-11` s; valid range: tr > 0; sets rise and fall smoothing for pulse and done.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_IDLE_CAPTURE`: exercise and make observable: A sampled high start while idle captures unsigned period3:period0, width3:width0, and count3:count0 on a rising clk crossing. Required traces: `time`, `clk`, `start`, `period0`, `period1`, `period2`, `period3`, `width0`, `width1`, `width2`, `width3`, `count0`, `count1`, `count2`, `count3`, `pulse`, `done`.
- `P_ZERO_CODE_MINIMUM`: exercise and make observable: A zero-coded period, width, or count is interpreted as one clock sample rather than zero. Required traces: `time`, `clk`, `period0`, `period1`, `period2`, `period3`, `width0`, `width1`, `width2`, `width3`, `count0`, `count1`, `count2`, `count3`, `pulse`, `done`.
- `P_PULSE_COUNT`: exercise and make observable: Each accepted command emits exactly the captured count number of pulses. Required traces: `time`, `clk`, `start`, `count0`, `count1`, `count2`, `count3`, `pulse`, `done`.
- `P_WIDTH_AND_PERIOD`: exercise and make observable: Each pulse remains high for the captured width in clock samples and pulse starts are separated by the captured period in clock samples. Required traces: `time`, `clk`, `period0`, `period1`, `period2`, `period3`, `width0`, `width1`, `width2`, `width3`, `pulse`.
- `P_COMPLETION`: exercise and make observable: After the final pulse completes, pulse is low and done is asserted. Required traces: `time`, `clk`, `pulse`, `done`.
- `P_OUTPUT_LEVELS`: exercise and make observable: pulse and done use 0 V and vdd levels with finite transition smoothing set by tr. Required traces: `time`, `pulse`, `done`.

The required trace names are: `time`, `clk`, `start`, `period0`, `period1`, `period2`, `period3`, `width0`, `width1`, `width2`, `width3`, `count0`, `count1`, `count2`, `count3`, `pulse`, `done`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
