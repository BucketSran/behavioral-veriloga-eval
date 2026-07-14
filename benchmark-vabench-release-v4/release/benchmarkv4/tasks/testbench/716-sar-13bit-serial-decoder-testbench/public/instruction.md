# SAR 13bit Serial Decoder Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `SAR 13bit Serial Decoder` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `sar_13bit_serial_decoder.va`:
  - Module `sar_13bit_serial_decoder` (entry)
    - position 0: `din` (input, electrical)
    - position 1: `clks` (input, electrical)
    - position 2: `ready` (input, electrical)
    - position 3: `dout` (output, electrical)
    - position 4: `dnum` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `sar_13bit_serial_decoder` as `XDUT` with ordered public binding: din=din, clks=clks, ready=ready, dout=dout, dnum=dnum.

## Public Parameter Contract

- `sar_13bit_serial_decoder.vth` defaults to `0.55`; valid range: finite; overrides vth.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_CONSUME_ONE_MSB_FIRST_BIT_ON`: exercise and make observable: Consume one MSB-first bit on each rising `ready` crossing, starting with bit 12 and ending with bit 0. Required traces: `time`, `clks`, `din`, `dnum`, `dout`, `ready`.
- `P_ADD_THE_CORRESPONDING_BINARY_WEIGHT_WHEN`: exercise and make observable: Add the corresponding binary weight when `din` is high. Required traces: `time`, `clks`, `din`, `dnum`, `dout`, `ready`.
- `P_INCREMENT_DNUM_FOR_EACH_HIGH_DECISION`: exercise and make observable: Increment `dnum` for each high decision in the current frame. Required traces: `time`, `clks`, `din`, `dnum`, `dout`, `ready`.
- `P_ON_EACH_RISING_CLKS_CROSSING_PUBLISH`: exercise and make observable: On each rising `clks` crossing, publish the previous frame as a normalized bipolar output. Required traces: `time`, `clks`, `din`, `dnum`, `dout`, `ready`.
- `P_MAP_AN_ALL_LOW_FRAME_TO`: exercise and make observable: Map an all-low frame to `-0.5` and an all-high frame near `+0.5`. Required traces: `time`, `clks`, `din`, `dnum`, `dout`, `ready`.
- `P_AFTER_PUBLISHING_RESET_THE_ACCUMULATOR_HIGH`: exercise and make observable: After publishing, reset the accumulator, high-bit count, and bit pointer for the next frame. Required traces: `time`, `clks`, `din`, `dnum`, `dout`, `ready`.

The required trace names are: `time`, `clks`, `din`, `dnum`, `dout`, `ready`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
