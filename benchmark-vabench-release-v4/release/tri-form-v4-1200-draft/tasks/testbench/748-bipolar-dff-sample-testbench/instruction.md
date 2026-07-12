# Bipolar DFF Sample Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Bipolar DFF Sample` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `bipolar_dff_sample.va`:
  - Module `bipolar_dff_sample` (entry)
    - position 0: `vin_d` (input, electrical)
    - position 1: `vclk` (input, electrical)
    - position 2: `vout_q` (output, electrical)
    - position 3: `vout_qbar` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `bipolar_dff_sample` as `XDUT` with ordered public binding: vin_d=vin_d, vclk=vclk, vout_q=vout_q, vout_qbar=vout_qbar.

## Public Parameter Contract

- `bipolar_dff_sample.vth` defaults to `0.0`; valid range: finite; overrides vth.
- `bipolar_dff_sample.vclk_th` defaults to `0.45`; valid range: finite; overrides vclk_th.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_EACH_RISING_CROSSING_OF_VCLK`: exercise and make observable: On each rising crossing of `vclk` through `vclk_th`, sample whether `vin_d` is above `vth`. Hold the sampled state between clock edges. Drive `vout_q` to `+1 V` for sampled high and `-1 V` for sampled low. Drive `vout_qbar` as the complementary bipolar output. Required traces: `time`, `vclk`, `vin_d`, `vout_q`, `vout_qbar`.
- `P_VTH_0_0_V_DATA_THRESHOLD`: exercise and make observable: `vth = 0.0 V`: data threshold for `vin_d`. Required traces: `time`, `vclk`, `vin_d`, `vout_q`, `vout_qbar`.
- `P_VCLK_TH_0_45_V_RISING`: exercise and make observable: `vclk_th = 0.45 V`: rising-edge threshold for `vclk`. Required traces: `time`, `vclk`, `vin_d`, `vout_q`, `vout_qbar`.
- `P_VTH_0_0_V_DATA_THRESHOLD_2`: exercise and make observable: - `vth = 0.0 V`: data threshold for `vin_d`. - `vclk_th = 0.45 V`: rising-edge threshold for `vclk`. Required traces: `time`, `vclk`, `vin_d`, `vout_q`, `vout_qbar`.
- `P_USE_DETERMINISTIC_VOLTAGE_DOMAIN_VERILOG_A`: exercise and make observable: Use deterministic voltage-domain Verilog-A and smooth voltage-coded output transitions. Do not emit a testbench, checker logic, out-of-band test hooks, hard-code testbench sample points, use current contributions, transistor-level devices, AC/noise analysis, `ddt()`, `idt()`, or simulator side channels. Required traces: `time`, `vclk`, `vin_d`, `vout_q`, `vout_qbar`.

The required trace names are: `time`, `vclk`, `vin_d`, `vout_q`, `vout_qbar`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
