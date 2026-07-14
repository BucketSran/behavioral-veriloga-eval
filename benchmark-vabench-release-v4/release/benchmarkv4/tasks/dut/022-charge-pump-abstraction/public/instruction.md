# Charge Pump Abstraction

## Task Contract

Implement the requested Verilog-A artifact for `Charge Pump Abstraction`.
- Form: `dut`
- Level: `L1`
- Category: `pll_clock_timing`
- Target artifact(s): `charge_pump_abstraction.va`

Implement `charge_pump_abstraction.va` in Verilog-A.

## Public Verilog-A Interface

```verilog
module charge_pump_abstraction(
    input  electrical clk,
    input  electrical rst,
    input  electrical up,
    input  electrical dn,
    output electrical vctrl,
    output electrical metric
);
```

## Public Parameter Contract

Provide these overrideable public parameters:

| Parameter | Default | Unit / Range | Contract |
| --- | ---: | --- | --- |
| `tr` | `100 ps` | time, `(0:inf)` | Rise/fall smoothing for `vctrl` and `metric`. |
| `vth` | `0.45` | V | Logic threshold for `clk`, `rst`, `up`, and `dn`. |
| `step` | `0.06` | V-equivalent update | Control-voltage increment/decrement per sampled UP/DN pulse. |
| `vmin` | `0.05` | V | Lower clamp for `vctrl`. |
| `vmax` | `0.85` | V | Upper clamp for `vctrl`. |

## Required Behavior

The module represents UP/DN pulse effects as a sampled voltage-domain control-node update without current-domain charge-pump contributions.

- Treat `clk`, `rst`, `up`, and `dn` as voltage-coded logic inputs.
- On rising `clk` edges, sample the UP/DN request when reset is low.
- A sampled UP-only pulse increases `vctrl` by `step`.
- A sampled DN-only pulse decreases `vctrl` by `step`.
- Simultaneous UP/DN or absent pulses hold the current control voltage.
- Clamp `vctrl` between `vmin` and `vmax`.
- When `rst` is high, reset `vctrl` to midscale.
- Drive `metric` as a voltage-coded status observable: 0.75 V for UP movement,
  0.15 V for DN movement, and 0.45 V for hold/reset.

## Modeling Constraints

Use voltage contributions only. Do not use current contributions, `ddt()`,
`idt()`, transistor-level devices, AC/noise analysis, validation logic, validation-only
test hooks, or simulator-specific side channels.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one source artifact named `charge_pump_abstraction.va`.
