# Clocked ADC3bit
## Task Contract
Implement `clocked_adc3bit.va`, a L1 voltage-domain data converter DUT for Clocked ADC3bit.
## Public Verilog-A Interface
Declare `module clocked_adc3bit(vd2, vd1, vd0, vin, vclk);` with scalar electrical ports. Port order is normative: `vd2` (output), `vd1` (output), `vd0` (output), `vin` (input), `vclk` (input).
## Public Parameter Contract
- `vth_clk = 0.45`: overrides vth_clk.
- `vh = 0.9`: overrides vh.

## Required Behavior
- `P_ON_EACH_RISING_CROSSING_OF_VCLK`: On each rising crossing of `vclk` through `vth_clk`, sample `vin` and quantize the `0 V` to `1 V` range into eight uniform lower-inclusive bins. Values below `0 V` clip to code `0`; values at or above `1 V` clip to code `7`. Drive `vd2`, `vd1`, and `vd0` as the binary representation of the held sampled code using `vh` for logic one and `0 V` for logic zero.
- `P_VTH_CLK_0_45_V_RISING`: `vth_clk = 0.45 V`: rising-edge threshold for `vclk`.
- `P_VH_0_9_V_LOGIC_HIGH`: `vh = 0.9 V`: logic-high output level.
- `P_VTH_CLK_0_45_V_RISING_2`: - `vth_clk = 0.45 V`: rising-edge threshold for `vclk`. - `vh = 0.9 V`: logic-high output level.
- `P_THE_OUTPUT_LOW_LEVEL_IS_0`: The output low level is `0 V`; the public input conversion range is `0 V` to `1 V`.
- `P_USE_DETERMINISTIC_VOLTAGE_DOMAIN_VERILOG_A`: Use deterministic voltage-domain Verilog-A and voltage contributions only. Do not emit a testbench, checker logic, out-of-band test hooks, file I/O, random behavior, current contributions, transistor-level devices, `ddt()`, `idt()`, or simulator side channels.

## Modeling Constraints
- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, reference-only implementation details, or simulator side channels.
- Do not emit a testbench, checker logic, undeclared probe nodes, hard-coded validation stimuli, waveform sample windows, or simulator side channels.
- Use only the public module interface, public parameters, and observable behavior specified here.

## Output Contract
Return exactly one source artifact named `clocked_adc3bit.va`. The candidate bundle must not require additional modules, nonstandard include files, or testbench changes.
