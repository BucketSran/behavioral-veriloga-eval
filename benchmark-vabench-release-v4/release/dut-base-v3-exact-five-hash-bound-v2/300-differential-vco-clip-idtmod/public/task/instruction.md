# Differential VCO With Clip And Idtmod

## Task Contract

Implement one behavioral Verilog-A DUT file named `differential_vco_clip_idtmod.va`.

This is a PLL clock-and-timing task following the common differential
behavioral VCO pattern: a differential control voltage sets a clipped
instantaneous frequency, wrapped phase is integrated with `idtmod()`, and two
opposite sine arms are driven around a common mode. Keep the model pure
voltage-domain behavioral Verilog-A: do not instantiate transistor-level
devices and do not use current-domain `I(...)` branch contributions.

## Public Verilog-A Interface

```verilog
module differential_vco_clip_idtmod (
    input  electrical vinp,
    input  electrical vinm,
    output electrical outp,
    output electrical outm,
    output electrical metric
);
```

## Public Parameter Contract

Public parameters and legal overrides:

| Parameter | Default | Unit / range | Contract |
| --- | ---: | --- | --- |
| `Fnom` | `20.0e6` | Hz, `(0:inf)` | Frequency at zero differential input. |
| `dFdV` | `160.0e6` | Hz/V, `(-inf:inf) exclude 0.0` | Frequency shift per volt of `V(vinp, vinm)`. |
| `Fmin` | `5.0e6` | Hz, `(0:inf)` | Lower clamp for the oscillation frequency. |
| `Fmax` | `80.0e6` | Hz, `(0:inf)` | Upper clamp for the oscillation frequency. |
| `Vcm` | `0.45` | V | Common-mode output center voltage. |
| `Vac` | `0.4` | V, `(0:inf)` | Per-arm sine amplitude. |

The supplied verification scenarios hold `V(vinp)` and `V(vinm)` constant so
the differential control is a fixed offset. At least one scenario drives the
raw frequency above the public clamp band, so the implemented oscillator must
use the clipped frequency rather than the unclipped expression.

## Required Behavior

Use `idtmod()` as a voltage-domain phase integrator whose instantaneous
frequency is set by the differential control voltage `V(vinp, vinm)`, clamp the
frequency into a legal band with a `clip` macro, and produce a fully
differential sine output.

This is a behavioral continuous-time task, not a conservative-current/KCL task.
Do not use `I(...)`, `ddt(...)`, or `idt(...)`.

The observable instantaneous frequency must equal `Fnom + dFdV * V(vinp,
vinm)` while that value lies inside `[Fmin, Fmax]`, and must remain at the
corresponding endpoint outside that band. Integrate this frequency with a
modulo-one `idtmod()` phase accumulator.

Drive `outp` and `outm` as equal-amplitude, opposite-polarity sine arms around
`Vcm`. Their common mode must remain at `Vcm`, each arm must have amplitude
`Vac`, and a rising zero crossing must recur at the clipped frequency. Expose
the wrapped phase as `metric`, linearly mapping phase zero to `0 V` and the
upper end of the modulo-one interval to `0.9 V`.

## Modeling Constraints

This is a PLL clock-and-timing task following the common differential
behavioral VCO pattern: a differential control voltage sets a clipped
instantaneous frequency, wrapped phase is integrated with `idtmod()`, and two
opposite sine arms are driven around a common mode. Keep the model pure
voltage-domain behavioral Verilog-A: do not instantiate transistor-level
devices and do not use current-domain `I(...)` branch contributions.

Keep the implementation behavioral and public-interface compatible. Do not add Spectre testbench code, simulator-specific hooks, or extra output artifacts.

## Output Contract

Return exactly one source artifact named `differential_vco_clip_idtmod.va`. Do
not generate a Spectre testbench for this task.
