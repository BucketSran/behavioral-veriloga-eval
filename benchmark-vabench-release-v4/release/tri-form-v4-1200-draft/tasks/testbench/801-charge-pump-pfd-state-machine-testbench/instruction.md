# Charge Pump PFD State Machine Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Charge Pump PFD State Machine` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `charge_pump_pfd_state_machine.va`:
  - Module `charge_pump_pfd_state_machine` (entry)
    - position 0: `ref` (input, electrical)
    - position 1: `fb` (input, electrical)
    - position 2: `vctrl` (output, electrical)
    - position 3: `metric` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `charge_pump_pfd_state_machine` as `XDUT` with ordered public binding: ref=ref, fb=fb, vctrl=vctrl, metric=metric.

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

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_AN_INTEGER_STATE_Q_HELD_IN`: exercise and make observable: An integer `state_q` held in `[-1, 0, +1]`, initialized to `0`. Required traces: `time`, `ref`, `fb`, `vctrl`, `metric`.
- `P_ON_EACH_RISING_CROSSING_OF_V`: exercise and make observable: On each rising crossing of `V(ref)` through `vth` (`@(cross(V(ref) - vth, +1))`), Required traces: `time`, `ref`, `fb`, `vctrl`, `metric`.
- `P_ON_EACH_RISING_CROSSING_OF_V_2`: exercise and make observable: On each rising crossing of `V(fb)` through `vth` (`@(cross(V(fb) - vth, +1))`), Required traces: `time`, `ref`, `fb`, `vctrl`, `metric`.
- `P_MAINTAIN_A_CONTROL_VOLTAGE_VCTRL_Q`: exercise and make observable: Maintain a control voltage `vctrl_q`, initialized to `vctrl_init`. On a fixed Required traces: `time`, `ref`, `fb`, `vctrl`, `metric`.
- `P_DRIVE_VCTRL_TRANSITION_VCTRL_Q_0`: exercise and make observable: Drive `vctrl = transition(vctrl_q, 0, tedge, tedge)`. Required traces: `time`, `ref`, `fb`, `vctrl`, `metric`.
- `P_DRIVE_METRIC_AS_A_VOLTAGE_CODED`: exercise and make observable: Drive `metric` as a voltage-coded copy of the detector state: Required traces: `time`, `ref`, `fb`, `vctrl`, `metric`.

The required trace names are: `time`, `ref`, `fb`, `vctrl`, `metric`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
