# Bipolar DFF Sample
## Task Contract
Implement `bipolar_dff_sample.va`, a L1 voltage-domain clock timing DUT for Bipolar DFF Sample.
## Public Verilog-A Interface
Declare `module bipolar_dff_sample(vin_d, vclk, vout_q, vout_qbar);` with scalar electrical ports. Port order is normative: `vin_d` (input), `vclk` (input), `vout_q` (output), `vout_qbar` (output).
## Public Parameter Contract
- `vth = 0.0`: overrides vth.
- `vclk_th = 0.45`: overrides vclk_th.

## Required Behavior
- `P_ON_EACH_RISING_CROSSING_OF_VCLK`: On each rising crossing of `vclk` through `vclk_th`, sample whether `vin_d` is above `vth`. Hold the sampled state between clock edges. Drive `vout_q` to `+1 V` for sampled high and `-1 V` for sampled low. Drive `vout_qbar` as the complementary bipolar output.
- `P_VTH_0_0_V_DATA_THRESHOLD`: `vth = 0.0 V`: data threshold for `vin_d`.
- `P_VCLK_TH_0_45_V_RISING`: `vclk_th = 0.45 V`: rising-edge threshold for `vclk`.
- `P_VTH_0_0_V_DATA_THRESHOLD_2`: - `vth = 0.0 V`: data threshold for `vin_d`. - `vclk_th = 0.45 V`: rising-edge threshold for `vclk`.
- `P_USE_DETERMINISTIC_VOLTAGE_DOMAIN_VERILOG_A`: Use deterministic voltage-domain Verilog-A and smooth voltage-coded output transitions. Do not emit a testbench, checker logic, out-of-band test hooks, hard-code testbench sample points, use current contributions, transistor-level devices, AC/noise analysis, `ddt()`, `idt()`, or simulator side channels.

## Modeling Constraints
- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, reference-only implementation details, or simulator side channels.
- Do not emit a testbench, checker logic, undeclared probe nodes, hard-coded validation stimuli, waveform sample windows, or simulator side channels.
- Use only the public module interface, public parameters, and observable behavior specified here.

## Output Contract
Return exactly one source artifact named `bipolar_dff_sample.va`. The candidate bundle must not require additional modules, nonstandard include files, or testbench changes.
