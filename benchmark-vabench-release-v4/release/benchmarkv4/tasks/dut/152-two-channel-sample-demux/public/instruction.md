# Two Channel Sample Demux

## Task Contract
Implement the Verilog-A DUT `two_channel_sample_demux.va` for two clocked analog sample sources driving one held output.

## Public Verilog-A Interface
Provide `module two_channel_sample_demux(samp1, samp2, clks1, clks2, vout);` with electrical inputs `samp1`, `samp2`, `clks1`, `clks2` and electrical output `vout`.

## Public Parameter Contract
Expose `parameter real vth = 0.45;`. Testbenches may override this threshold.

## Required Behavior
On a rising crossing of `clks1` through `vth`, sample `samp1` into the output register. On a rising crossing of `clks2` through `vth`, sample `samp2` into the output register. Hold the most recently sampled value on `vout` between events.

## Modeling Constraints
Use event-driven state updates from both clock inputs. Do not swap channels, ignore the second channel, apply half output gain, or continuously track either input.

## Output Contract
Submit only the completed Verilog-A module in `two_channel_sample_demux.va`.
