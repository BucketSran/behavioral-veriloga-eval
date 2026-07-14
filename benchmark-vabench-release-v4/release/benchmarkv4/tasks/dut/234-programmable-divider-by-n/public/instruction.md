# Programmable Divider By N

## Task Contract
Implement `programmable_divider_by_n.va`, a single voltage-domain DUT for a programmable clock divider. This is a clock/control L1 component, not a testbench or a composed L2 flow.

## Public Verilog-A Interface
Declare module `programmable_divider_by_n(clk, divctrl, out)` with scalar electrical ports. `clk` is a voltage-coded clock input, `divctrl` is an analog-coded divide-ratio control input, and `out` is the voltage-coded divider output.

## Public Parameter Contract
Provide overrideable public parameters:

- `vth = 0.45 V`: rising-edge threshold for `clk`.
- `vh = 0.9 V`: logic-high output level for `out`.

The output low level is `0 V`.

## Required Behavior
Detect rising crossings of `clk` through `vth`. At each qualifying edge, interpret `divctrl` as the requested divide ratio by rounding it to the nearest integer; clip ratios below one to one. Maintain an internal modulo counter for the current ratio and drive `out` high only when the counter state is zero, low otherwise. For a requested ratio of three, the output is high once every three input clock edges.

## Modeling Constraints
Use deterministic voltage-domain Verilog-A and smooth the voltage-coded output transitions. Do not emit a testbench, checker logic, out-of-band test hooks, waveform files, current contributions, transistor-level devices, `ddt()`, `idt()`, or simulator side channels.

## Output Contract
Return exactly one source artifact named `programmable_divider_by_n.va`.
