# Clocked Mux4 Sampler Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Clocked Mux4 Sampler` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `clocked_mux4_sampler.va`:
  - Module `clocked_mux4_sampler` (entry)
    - position 0: `dsel0` (input, electrical)
    - position 1: `dsel1` (input, electrical)
    - position 2: `din0` (input, electrical)
    - position 3: `din1` (input, electrical)
    - position 4: `din2` (input, electrical)
    - position 5: `din3` (input, electrical)
    - position 6: `update` (input, electrical)
    - position 7: `rst` (input, electrical)
    - position 8: `clks` (input, electrical)
    - position 9: `dout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `clocked_mux4_sampler` as `XDUT` with ordered public binding: dsel0=dsel0, dsel1=dsel1, din0=din0, din1=din1, din2=din2, din3=din3, update=update, rst=rst, clks=clks, dout=dout.

## Public Parameter Contract

- `clocked_mux4_sampler.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `clocked_mux4_sampler.tdel` defaults to `1p`; valid range: finite; overrides tdel.
- `clocked_mux4_sampler.tr` defaults to `20p`; valid range: finite; overrides tr.
- `clocked_mux4_sampler.tf` defaults to `20p`; valid range: finite; overrides tf.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_SELECTS_DIN0`: exercise and make observable: While `rst` is high, the selected channel and `dout` are forced to `din0`. Required traces: `time`, `clks`, `din0`, `din1`, `din2`, `din3`, `dout`, `dsel0`, `dsel1`, `rst`, `update`.
- `P_FALLING_CLOCK_UPDATE_SAMPLE`: exercise and make observable: On each falling `clks` crossing with reset inactive and `update` high, latch `dsel0/dsel1` and sample the selected input. Required traces: `time`, `clks`, `din0`, `din1`, `din2`, `din3`, `dout`, `dsel0`, `dsel1`, `rst`, `update`.
- `P_UPDATE_LOW_HOLDS_STATE`: exercise and make observable: On falling `clks` crossings with `update` low, hold the previous selection and output value. Required traces: `time`, `clks`, `din0`, `din1`, `din2`, `din3`, `dout`, `dsel0`, `dsel1`, `rst`, `update`.
- `P_SELECT_DECODE_AND_OUTPUT_TIMING`: exercise and make observable: The held two-bit selection maps to `din0..din3` in binary order and drives `dout` with the declared transition timing. Required traces: `time`, `clks`, `din0`, `din1`, `din2`, `din3`, `dout`, `dsel0`, `dsel1`, `rst`, `update`.

The required trace names are: `time`, `clks`, `din0`, `din1`, `din2`, `din3`, `dout`, `dsel0`, `dsel1`, `rst`, `update`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
