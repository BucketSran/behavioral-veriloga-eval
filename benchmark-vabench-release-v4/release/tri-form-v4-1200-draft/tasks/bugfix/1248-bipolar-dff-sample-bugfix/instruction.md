# Bipolar DFF Sample Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `bipolar_dff_sample.va`:
  - Module `bipolar_dff_sample` (entry)
    - position 0: `vin_d` (input, electrical)
    - position 1: `vclk` (input, electrical)
    - position 2: `vout_q` (output, electrical)
    - position 3: `vout_qbar` (output, electrical)

## Public Parameter Contract

- `bipolar_dff_sample.vth` defaults to `0.0`; valid range: finite; overrides vth.
- `bipolar_dff_sample.vclk_th` defaults to `0.45`; valid range: finite; overrides vclk_th.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_EACH_RISING_CROSSING_OF_VCLK`: restore: On each rising crossing of `vclk` through `vclk_th`, sample whether `vin_d` is above `vth`. Hold the sampled state between clock edges. Drive `vout_q` to `+1 V` for sampled high and `-1 V` for sampled low. Drive `vout_qbar` as the complementary bipolar output. Required traces: `time`, `vclk`, `vin_d`, `vout_q`, `vout_qbar`.
- `P_VTH_0_0_V_DATA_THRESHOLD`: restore: `vth = 0.0 V`: data threshold for `vin_d`. Required traces: `time`, `vclk`, `vin_d`, `vout_q`, `vout_qbar`.
- `P_VCLK_TH_0_45_V_RISING`: restore: `vclk_th = 0.45 V`: rising-edge threshold for `vclk`. Required traces: `time`, `vclk`, `vin_d`, `vout_q`, `vout_qbar`.
- `P_VTH_0_0_V_DATA_THRESHOLD_2`: restore: - `vth = 0.0 V`: data threshold for `vin_d`. - `vclk_th = 0.45 V`: rising-edge threshold for `vclk`. Required traces: `time`, `vclk`, `vin_d`, `vout_q`, `vout_qbar`.
- `P_USE_DETERMINISTIC_VOLTAGE_DOMAIN_VERILOG_A`: restore: Use deterministic voltage-domain Verilog-A and smooth voltage-coded output transitions. Do not emit a testbench, checker logic, out-of-band test hooks, hard-code testbench sample points, use current contributions, transistor-level devices, AC/noise analysis, `ddt()`, `idt()`, or simulator side channels. Required traces: `time`, `vclk`, `vin_d`, `vout_q`, `vout_qbar`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `bipolar_dff_sample.va`.
Every supplied `.va` file is editable; do not add or omit files.
