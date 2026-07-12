# Four Channel Edge Sampler Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Four Channel Edge Sampler` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `four_channel_edge_sampler.va`:
  - Module `four_channel_edge_sampler` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `vin0` (input, electrical)
    - position 2: `vin1` (input, electrical)
    - position 3: `vin2` (input, electrical)
    - position 4: `vin3` (input, electrical)
    - position 5: `vout0` (output, electrical)
    - position 6: `vout1` (output, electrical)
    - position 7: `vout2` (output, electrical)
    - position 8: `vout3` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `four_channel_edge_sampler` as `XDUT` with ordered public binding: clk=clk, vin0=vin0, vin1=vin1, vin2=vin2, vin3=vin3, vout0=vout0, vout1=vout1, vout2=vout2, vout3=vout3.

## Public Parameter Contract

- `four_channel_edge_sampler.direction` defaults to `1`; valid range: finite; overrides direction.
- `four_channel_edge_sampler.vdd` defaults to `1.2`; valid range: finite; overrides vdd.
- `four_channel_edge_sampler.tr` defaults to `50p`; valid range: finite; overrides tr.
- `four_channel_edge_sampler.tf` defaults to `50p`; valid range: finite; overrides tf.
- `four_channel_edge_sampler.td` defaults to `0`; valid range: finite; overrides td.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_CONFIGURED_EDGE_SIMULTANEOUS_SAMPLE`: exercise and make observable: The configured `clk` crossing direction samples `vin0` through `vin3` simultaneously and updates all held outputs together. Required traces: `time`, `clk`, `vin0`, `vin1`, `vin2`, `vin3`, `vout0`, `vout1`, `vout2`, `vout3`.
- `P_CHANNEL_MAPPING`: exercise and make observable: Each sampled input channel maps to the same-numbered output channel without swaps. Required traces: `time`, `clk`, `vin0`, `vin1`, `vin2`, `vin3`, `vout0`, `vout1`, `vout2`, `vout3`.
- `P_OUTPUT_GAIN_AND_HOLD`: exercise and make observable: Each `vout` holds the sampled amplitude without gain scaling until the next sampling edge. Required traces: `time`, `clk`, `vin0`, `vin1`, `vin2`, `vin3`, `vout0`, `vout1`, `vout2`, `vout3`.

The required trace names are: `time`, `clk`, `vin0`, `vin1`, `vin2`, `vin3`, `vout0`, `vout1`, `vout2`, `vout3`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
