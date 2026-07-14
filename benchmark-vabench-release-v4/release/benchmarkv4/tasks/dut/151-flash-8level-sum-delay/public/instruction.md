# Flash 8level Sum Delay

## Task Contract
Implement the Verilog-A DUT `flash_8level_sum_delay.va` for a differential 8-level flash threshold summarizer with a one-cycle delayed summary output.

## Public Verilog-A Interface
Provide `module flash_8level_sum_delay(vip, vim, clks, reset, refp, refn, doutsum, doutsumdelay);` with electrical inputs `vip`, `vim`, `clks`, `reset`, `refp`, `refn` and electrical outputs `doutsum`, `doutsumdelay`.

## Public Parameter Contract
Expose real parameters `vth = 0.45`, `ref_scaling = 0.5`, and `tt = 10p`. Testbenches may override these parameters.

## Required Behavior
On each rising crossing of `clks` through `vth`, compare `V(vip, vim)` against eight symmetric thresholds derived from `V(refp)-V(refn)`, `ref_scaling`, and the 1/8, 3/8, 5/8, and 7/8 flash tap positions. Drive `doutsum` with the current asserted-threshold fraction and `doutsumdelay` with the previous conversion's fraction. The `reset` port is present for interface compatibility and is not part of the state update.

## Modeling Constraints
Use event-driven flash counting and retained previous-sum state. Do not use the wrong reference scaling, make the delayed output equal to the current output, or omit normalization by the eight threshold decisions.

## Output Contract
Submit only the completed Verilog-A module in `flash_8level_sum_delay.va`.
