# Polyphase I/Q Balance Monitor Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

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

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_DISABLED_DRIVE`: restore: On reset or when disabled, drive outputs to `vcm` and clear metrics. Required traces: `time`, `i_in`, `q_in`, `clk`, `rst`, `enable`, `i_out`, `q_out`, `amp_error_metric`, `phase_error_metric`, `balanced`.
- `P_ON_EACH_ENABLED_RISING_CLK_EDGE`: restore: On each enabled rising `clk` edge, sample I and Q input deviations around `vcm`. Required traces: `time`, `i_in`, `q_in`, `clk`, `rst`, `enable`, `i_out`, `q_out`, `amp_error_metric`, `phase_error_metric`, `balanced`.
- `P_DRIVE_CORRECTED_I_Q_OUTPUTS_WITH`: restore: Drive corrected I/Q outputs with bounded amplitude normalization. Required traces: `time`, `i_in`, `q_in`, `clk`, `rst`, `enable`, `i_out`, `q_out`, `amp_error_metric`, `phase_error_metric`, `balanced`.
- `P_EXPOSE_AMPLITUDE_AND_PHASE_ERROR_PROXIES`: restore: Expose amplitude and phase-error proxies as separate voltage-domain metrics. Required traces: `time`, `i_in`, `q_in`, `clk`, `rst`, `enable`, `i_out`, `q_out`, `amp_error_metric`, `phase_error_metric`, `balanced`.
- `P_ASSERT_BALANCED_ONLY_WHEN_BOTH_METRICS`: restore: Assert `balanced` only when both metrics remain below their thresholds for two updates. Required traces: `time`, `i_in`, `q_in`, `clk`, `rst`, `enable`, `i_out`, `q_out`, `amp_error_metric`, `phase_error_metric`, `balanced`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `polyphase_iq_balance_monitor_top.va`, `iq_normalizer.va`, `balance_metric_core.va`.
Every supplied `.va` file is editable; do not add or omit files.
