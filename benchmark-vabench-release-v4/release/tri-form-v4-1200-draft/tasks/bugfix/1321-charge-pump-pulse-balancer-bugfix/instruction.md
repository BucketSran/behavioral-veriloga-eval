# Charge-pump Pulse Balancer Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `charge_pump_pulse_balancer.va`:
  - Module `charge_pump_pulse_balancer` (entry)
    - position 0: `up` (input, electrical)
    - position 1: `dn` (input, electrical)
    - position 2: `clk` (input, electrical)
    - position 3: `rst` (input, electrical)
    - position 4: `enable` (input, electrical)
    - position 5: `vctrl` (output, electrical)
    - position 6: `imbalance_metric` (output, electrical)
    - position 7: `balanced` (output, electrical)

## Public Parameter Contract

- `charge_pump_pulse_balancer.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `charge_pump_pulse_balancer.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `charge_pump_pulse_balancer.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `charge_pump_pulse_balancer.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `charge_pump_pulse_balancer.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `charge_pump_pulse_balancer.pump_step` defaults to `20e-3 from (0:inf)` V; valid range: positive; overrides pump_step.
- `charge_pump_pulse_balancer.balance_tol` defaults to `30e-3 from (0:inf)` V; valid range: positive; overrides balance_tol.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_DISABLED_DRIVE`: restore: On reset or when disabled, drive `vctrl` to `vcm`, clear imbalance, and clear `balanced`. Required traces: `time`, `up`, `dn`, `clk`, `rst`, `enable`, `vctrl`, `imbalance_metric`, `balanced`.
- `P_ON_EACH_RISING_CLK_EDGE_OBSERVE`: restore: On each rising `clk` edge, observe voltage-coded `up` and `dn` pulse states. Required traces: `time`, `up`, `dn`, `clk`, `rst`, `enable`, `vctrl`, `imbalance_metric`, `balanced`.
- `P_INCREASE_VCTRL_FOR_UP_ONLY_DECREASE`: restore: Increase `vctrl` for UP-only, decrease it for DN-only, and hold for simultaneous or inactive pulses. Required traces: `time`, `up`, `dn`, `clk`, `rst`, `enable`, `vctrl`, `imbalance_metric`, `balanced`.
- `P_DRIVE_IMBALANCE_METRIC_FROM_THE_ACCUMULATED`: restore: Drive `imbalance_metric` from the accumulated UP-minus-DN activity. Required traces: `time`, `up`, `dn`, `clk`, `rst`, `enable`, `vctrl`, `imbalance_metric`, `balanced`.
- `P_ASSERT_BALANCED_ONLY_WHEN_THE_RECENT`: restore: Assert `balanced` only when the recent absolute imbalance is below `balance_tol`. Required traces: `time`, `up`, `dn`, `clk`, `rst`, `enable`, `vctrl`, `imbalance_metric`, `balanced`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `charge_pump_pulse_balancer.va`.
Every supplied `.va` file is editable; do not add or omit files.
