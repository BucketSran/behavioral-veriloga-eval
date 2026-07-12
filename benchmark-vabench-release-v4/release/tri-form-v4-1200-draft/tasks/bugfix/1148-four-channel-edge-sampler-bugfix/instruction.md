# Four Channel Edge Sampler Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

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

## Public Parameter Contract

- `four_channel_edge_sampler.direction` defaults to `1`; valid range: finite; overrides direction.
- `four_channel_edge_sampler.vdd` defaults to `1.2`; valid range: finite; overrides vdd.
- `four_channel_edge_sampler.tr` defaults to `50p`; valid range: finite; overrides tr.
- `four_channel_edge_sampler.tf` defaults to `50p`; valid range: finite; overrides tf.
- `four_channel_edge_sampler.td` defaults to `0`; valid range: finite; overrides td.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_CONFIGURED_EDGE_SIMULTANEOUS_SAMPLE`: restore: The configured `clk` crossing direction samples `vin0` through `vin3` simultaneously and updates all held outputs together. Required traces: `time`, `clk`, `vin0`, `vin1`, `vin2`, `vin3`, `vout0`, `vout1`, `vout2`, `vout3`.
- `P_CHANNEL_MAPPING`: restore: Each sampled input channel maps to the same-numbered output channel without swaps. Required traces: `time`, `clk`, `vin0`, `vin1`, `vin2`, `vin3`, `vout0`, `vout1`, `vout2`, `vout3`.
- `P_OUTPUT_GAIN_AND_HOLD`: restore: Each `vout` holds the sampled amplitude without gain scaling until the next sampling edge. Required traces: `time`, `clk`, `vin0`, `vin1`, `vin2`, `vin3`, `vout0`, `vout1`, `vout2`, `vout3`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `four_channel_edge_sampler.va`.
Every supplied `.va` file is editable; do not add or omit files.
