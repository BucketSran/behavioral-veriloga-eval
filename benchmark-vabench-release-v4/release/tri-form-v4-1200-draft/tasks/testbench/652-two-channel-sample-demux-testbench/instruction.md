# Two Channel Sample Demux Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Two Channel Sample Demux` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `two_channel_sample_demux.va`:
  - Module `two_channel_sample_demux` (entry)
    - position 0: `samp1` (input, electrical)
    - position 1: `samp2` (input, electrical)
    - position 2: `clks1` (input, electrical)
    - position 3: `clks2` (input, electrical)
    - position 4: `vout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `two_channel_sample_demux` as `XDUT` with ordered public binding: samp1=samp1, samp2=samp2, clks1=clks1, clks2=clks2, vout=vout.

## Public Parameter Contract

- `two_channel_sample_demux.vth` defaults to `0.45`; valid range: finite; overrides vth.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_CLOCKED_CHANNEL_SELECTION`: exercise and make observable: A rising `clks1` crossing samples `samp1` and a rising `clks2` crossing samples `samp2` into the shared held output. Required traces: `time`, `clks1`, `clks2`, `samp1`, `samp2`, `vout`.
- `P_BOTH_CHANNELS_REACHABLE`: exercise and make observable: Both clocked sample channels can independently update `vout` without one channel masking the other. Required traces: `time`, `clks1`, `clks2`, `samp1`, `samp2`, `vout`.
- `P_OUTPUT_GAIN_AND_HOLD`: exercise and make observable: `vout` holds the selected sample amplitude without gain scaling between clock events. Required traces: `time`, `clks1`, `clks2`, `samp1`, `samp2`, `vout`.

The required trace names are: `time`, `clks1`, `clks2`, `samp1`, `samp2`, `vout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
