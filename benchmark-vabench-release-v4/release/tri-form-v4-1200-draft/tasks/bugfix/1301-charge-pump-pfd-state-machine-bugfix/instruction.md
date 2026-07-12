# Charge Pump PFD State Machine Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `charge_pump_pfd_state_machine.va`:
  - Module `charge_pump_pfd_state_machine` (entry)
    - position 0: `ref` (input, electrical)
    - position 1: `fb` (input, electrical)
    - position 2: `vctrl` (output, electrical)
    - position 3: `metric` (output, electrical)

## Public Parameter Contract

- `charge_pump_pfd_state_machine.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `charge_pump_pfd_state_machine.tstep` defaults to `1.0e-9 from (0:inf)`; valid range: finite; overrides tstep.
- `charge_pump_pfd_state_machine.pump_rate` defaults to `60.0e6 from [0:inf)`; valid range: finite; overrides pump_rate.
- `charge_pump_pfd_state_machine.vctrl_init` defaults to `0.45`; valid range: finite; overrides vctrl_init.
- `charge_pump_pfd_state_machine.vctrl_min` defaults to `0.05`; valid range: finite; overrides vctrl_min.
- `charge_pump_pfd_state_machine.vctrl_max` defaults to `0.85`; valid range: finite; overrides vctrl_max.
- `charge_pump_pfd_state_machine.tedge` defaults to `200p from (0:inf)`; valid range: finite; overrides tedge.
- `charge_pump_pfd_state_machine.metric_lo` defaults to `0.1`; valid range: finite; overrides metric_lo.
- `charge_pump_pfd_state_machine.metric_mid` defaults to `0.45`; valid range: finite; overrides metric_mid.
- `charge_pump_pfd_state_machine.metric_hi` defaults to `0.8`; valid range: finite; overrides metric_hi.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_AN_INTEGER_STATE_Q_HELD_IN`: restore: An integer `state_q` held in `[-1, 0, +1]`, initialized to `0`. Required traces: `time`, `ref`, `fb`, `vctrl`, `metric`.
- `P_ON_EACH_RISING_CROSSING_OF_V`: restore: On each rising crossing of `V(ref)` through `vth` (`@(cross(V(ref) - vth, +1))`), Required traces: `time`, `ref`, `fb`, `vctrl`, `metric`.
- `P_ON_EACH_RISING_CROSSING_OF_V_2`: restore: On each rising crossing of `V(fb)` through `vth` (`@(cross(V(fb) - vth, +1))`), Required traces: `time`, `ref`, `fb`, `vctrl`, `metric`.
- `P_MAINTAIN_A_CONTROL_VOLTAGE_VCTRL_Q`: restore: Maintain a control voltage `vctrl_q`, initialized to `vctrl_init`. On a fixed Required traces: `time`, `ref`, `fb`, `vctrl`, `metric`.
- `P_DRIVE_VCTRL_TRANSITION_VCTRL_Q_0`: restore: Drive `vctrl = transition(vctrl_q, 0, tedge, tedge)`. Required traces: `time`, `ref`, `fb`, `vctrl`, `metric`.
- `P_DRIVE_METRIC_AS_A_VOLTAGE_CODED`: restore: Drive `metric` as a voltage-coded copy of the detector state: Required traces: `time`, `ref`, `fb`, `vctrl`, `metric`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `charge_pump_pfd_state_machine.va`.
Every supplied `.va` file is editable; do not add or omit files.
