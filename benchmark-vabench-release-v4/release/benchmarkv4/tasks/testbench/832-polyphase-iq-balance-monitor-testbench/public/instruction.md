# Polyphase I/Q Balance Monitor Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Polyphase I/Q Balance Monitor` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `polyphase_iq_balance_monitor_top.va`:
  - Module `polyphase_iq_balance_monitor_top` (entry)
    - position 0: `i_in` (inout, electrical)
    - position 1: `q_in` (inout, electrical)
    - position 2: `clk` (inout, electrical)
    - position 3: `rst` (inout, electrical)
    - position 4: `enable` (inout, electrical)
    - position 5: `i_out` (inout, electrical)
    - position 6: `q_out` (inout, electrical)
    - position 7: `amp_error_metric` (inout, electrical)
    - position 8: `phase_error_metric` (inout, electrical)
    - position 9: `balanced` (inout, electrical)
- Artifact `iq_normalizer.va`:
  - Module `iq_normalizer` (required_submodule)
    - position 0: `i_sample` (inout, electrical)
    - position 1: `q_sample` (inout, electrical)
    - position 2: `i_norm` (inout, electrical)
    - position 3: `q_norm` (inout, electrical)
- Artifact `balance_metric_core.va`:
  - Module `balance_metric_core` (required_submodule)
    - position 0: `i_sample` (inout, electrical)
    - position 1: `q_sample` (inout, electrical)
    - position 2: `amp_error_metric` (inout, electrical)
    - position 3: `phase_error_metric` (inout, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `polyphase_iq_balance_monitor_top` as `XDUT` with ordered public binding: i_in=i_in, q_in=q_in, clk=clk, rst=rst, enable=enable, i_out=i_out, q_out=q_out, amp_error_metric=amp_error_metric, phase_error_metric=phase_error_metric, balanced=balanced.

## Public Parameter Contract

- `polyphase_iq_balance_monitor_top.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `polyphase_iq_balance_monitor_top.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `polyphase_iq_balance_monitor_top.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `polyphase_iq_balance_monitor_top.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `polyphase_iq_balance_monitor_top.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `polyphase_iq_balance_monitor_top.amp_tol` defaults to `45e-3`; valid range: finite; overrides amp_tol.
- `polyphase_iq_balance_monitor_top.phase_tol` defaults to `60e-3`; valid range: finite; overrides phase_tol.
- `iq_normalizer.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `iq_normalizer.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `iq_normalizer.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `iq_normalizer.target_dev` defaults to `0.22`; valid range: finite; overrides target_dev.
- `iq_normalizer.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `balance_metric_core.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `balance_metric_core.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `balance_metric_core.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `balance_metric_core.amp_tol` defaults to `45e-3`; valid range: finite; overrides amp_tol.
- `balance_metric_core.phase_tol` defaults to `60e-3`; valid range: finite; overrides phase_tol.
- `balance_metric_core.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_RESET_OR_WHEN_DISABLED_DRIVE`: exercise and make observable: On reset or when disabled, drive outputs to `vcm` and clear metrics. Required traces: `time`, `i_in`, `q_in`, `clk`, `rst`, `enable`, `i_out`, `q_out`, `amp_error_metric`, `phase_error_metric`, `balanced`.
- `P_ON_EACH_ENABLED_RISING_CLK_EDGE`: exercise and make observable: On each enabled rising `clk` edge, sample I and Q input deviations around `vcm`. Required traces: `time`, `i_in`, `q_in`, `clk`, `rst`, `enable`, `i_out`, `q_out`, `amp_error_metric`, `phase_error_metric`, `balanced`.
- `P_DRIVE_CORRECTED_I_Q_OUTPUTS_WITH`: exercise and make observable: Drive corrected I/Q outputs with bounded amplitude normalization. Required traces: `time`, `i_in`, `q_in`, `clk`, `rst`, `enable`, `i_out`, `q_out`, `amp_error_metric`, `phase_error_metric`, `balanced`.
- `P_EXPOSE_AMPLITUDE_AND_PHASE_ERROR_PROXIES`: exercise and make observable: Expose amplitude and phase-error proxies as separate voltage-domain metrics. Required traces: `time`, `i_in`, `q_in`, `clk`, `rst`, `enable`, `i_out`, `q_out`, `amp_error_metric`, `phase_error_metric`, `balanced`.
- `P_ASSERT_BALANCED_ONLY_WHEN_BOTH_METRICS`: exercise and make observable: Assert `balanced` only when both metrics remain below their thresholds for two updates. Required traces: `time`, `i_in`, `q_in`, `clk`, `rst`, `enable`, `i_out`, `q_out`, `amp_error_metric`, `phase_error_metric`, `balanced`.

The required trace names are: `time`, `i_in`, `q_in`, `clk`, `rst`, `enable`, `i_out`, `q_out`, `amp_error_metric`, `phase_error_metric`, `balanced`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
