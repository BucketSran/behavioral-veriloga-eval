# Iterative ISAR DAC

## Task Contract

- Form: `dut`.
- Level: `L1`.
- Category: data-converter calibration/search primitive.
- Target artifact: `iterative_isar_dac.va`.
- Role: iterative comparison-directed DAC search.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module iterative_isar_dac(dcmp, rst, clk, vdac);
```

All ports are electrical. `dcmp` is the comparator decision, `rst` resets the search, `clk` advances the iteration, and `vdac` is the searched DAC voltage.

## Public Parameter Contract

Provide overrideable parameters `vth = 0.5`, `tr = 100p`, `range = 0.1`, `lsb = 10u`, and `radix = 2`. Use `vth` for logic decisions and `tr` for output transition shaping.

## Required Behavior

At initialization and reset, set `vdac` to zero and set the search step to `range`. On each rising `clk` crossing while the step remains above `lsb`, update `vdac` according to the comparator decision: if `dcmp > vth`, subtract the current step from `vdac`; if `dcmp <= vth`, add the current step to `vdac`. After each update, divide the step by `radix`. Hold the DAC value after the step reaches the LSB limit.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `iterative_isar_dac.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
