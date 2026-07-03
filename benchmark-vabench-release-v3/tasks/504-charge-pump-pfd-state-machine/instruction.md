# Charge Pump PFD State Machine

Implement one behavioral Verilog-A DUT file named `charge_pump_pfd_state_machine.va`.

This is a PLL clock-and-timing task recast from the Cadence `chargepump.va`
example (`VerilogA/Vloga_M05_VlogaModelDesc/chargepump.va`). That original uses
an `@cross`-driven integer phase-detector state machine and a structural RC loop
filter with current-domain contributions. This recast keeps the `@cross`-driven
tri-state phase-detector state machine but expresses the loop-filter integration
as a pure voltage-domain sampled update, with no current contributions and no
instantiated devices.

## Interface

```verilog
module charge_pump_pfd_state_machine (
    input  electrical ref,
    input  electrical fb,
    output electrical vctrl,
    output electrical metric
);
```

## Required Behavior

Implement a classic three-state phase-frequency detector as a voltage-domain
event-driven state machine, and integrate its output onto a bounded control
voltage.

This is a behavioral continuous-time task, not a conservative-current/KCL task.
Do not use `I(...)`, `ddt(...)`, or `idt(...)`.

Use voltage-coded logic levels with high inputs near `0.9 V` and low inputs near
`0.0 V`, threshold `vth = 0.45 V`.

Implement:

- An integer `state_q` held in `[-1, 0, +1]`, initialized to `0`.
- On each rising crossing of `V(ref)` through `vth` (`@(cross(V(ref) - vth, +1))`),
  increment `state_q` but clamp it to `+1`.
- On each rising crossing of `V(fb)` through `vth` (`@(cross(V(fb) - vth, +1))`),
  decrement `state_q` but clamp it to `-1`.
- Maintain a control voltage `vctrl_q`, initialized to `vctrl_init`. On a fixed
  `tstep` timer (`@(timer(0, tstep))`), update
  `vctrl_q = vctrl_q + state_q * pump_rate * tstep`, then clamp `vctrl_q` into
  `[vctrl_min, vctrl_max]`.
- Drive `vctrl = transition(vctrl_q, 0, tedge, tedge)`.
- Drive `metric` as a voltage-coded copy of the detector state:
  `metric = transition((state_q < 0) ? metric_lo : (state_q > 0) ? metric_hi : metric_mid, 0, tedge, tedge)`.

Public parameters and legal overrides:

| Parameter | Default | Unit / range | Contract |
| --- | ---: | --- | --- |
| `vth` | `0.45` | V | Logic decision threshold. |
| `tstep` | `1.0e-9` | s, `(0:inf)` | Control-voltage integration timestep. |
| `pump_rate` | `60.0e6` | V/s, `[0:inf)` | Control-voltage slew rate per unit state. |
| `vctrl_init` | `0.45` | V | Initial control voltage. |
| `vctrl_min` | `0.05` | V | Lower clamp for the control voltage. |
| `vctrl_max` | `0.85` | V | Upper clamp for the control voltage. |
| `tedge` | `200p` | s, `(0:inf)` | Output smoothing time. |
| `metric_lo` | `0.1` | V | Metric voltage for state `-1`. |
| `metric_mid` | `0.45` | V | Metric voltage for state `0`. |
| `metric_hi` | `0.8` | V | Metric voltage for state `+1`. |

The verification harness drives `ref` and `fb` as same-frequency clock waves with
a fixed phase offset, so the detector state repeatedly takes a consistent sign
and the control voltage ramps monotonically toward the corresponding rail.
Over such a window `vctrl` is expected to move in the direction implied by the
lead/lag relation (reference leading feedback ramps toward `vctrl_max`;
feedback leading reference ramps toward `vctrl_min`) and `metric` is expected to
report the detector-state polarity.

## Support clock (`ref_fb_clk.va`)

This task supplies a companion support artifact `ref_fb_clk.va` that generates
the two phase-offset clock waves; the harness authors it and you do not. Its
public contract is:

```verilog
module ref_fb_clk (inout VDD, inout VSS, output ref, output fb);
    parameter real period      = 200n from (0:inf);
    parameter real phase_lead  = 20n  from [0:inf);
    parameter real tedge       = 100p from (0:inf);
endmodule
```

`ref` and `fb` are equal-period square waves swinging `VSS..VDD`. `phase_lead >= 0`
shifts `fb` later than `ref` by that amount (so a positive `phase_lead` means
**reference leads feedback**). The candidate DUT must operate correctly for any
legal `phase_lead` override in `[0:inf)`.

## Output

Return exactly one source artifact named `charge_pump_pfd_state_machine.va`. Do
not generate a Spectre testbench or the support clock for this task.
