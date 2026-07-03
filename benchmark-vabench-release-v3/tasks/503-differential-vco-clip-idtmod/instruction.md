# Differential VCO With Clip And Idtmod

Implement one behavioral Verilog-A DUT file named `differential_vco_clip_idtmod.va`.

This is a PLL clock-and-timing task recast from the Cadence `VCO_ams.vams`
example (`BehavModelVAMS_M08_Operation/.solutions/VCO_ams.vams`). Keep the model
pure voltage-domain behavioral Verilog-A: do not instantiate transistor-level
devices and do not use current-domain `I(...)` branch contributions.

## Interface

```verilog
module differential_vco_clip_idtmod (
    input  electrical vinp,
    input  electrical vinm,
    output electrical outp,
    output electrical outm,
    output electrical metric
);
```

## Required Behavior

Use `idtmod()` as a voltage-domain phase integrator whose instantaneous
frequency is set by the differential control voltage `V(vinp, vinm)`, clamp the
frequency into a legal band with a `clip` macro, and produce a fully
differential sine output.

This is a behavioral continuous-time task, not a conservative-current/KCL task.
Do not use `I(...)`, `ddt(...)`, or `idt(...)`.

Define a clip macro at file scope:

```verilog
`define clip(x, LO, HI) ((x < LO) ? LO : (x > HI) ? HI : x)
```

Implement:

- `freq_q = `clip(Fnom + dFdV * V(vinp, vinm), Fmin, Fmax)`
- `phase_q = idtmod(freq_q, 0.0, 1.0)` (modulo-1 phase accumulator)
- `outp = Vcm + Vac * sin(M_TWO_PI * phase_q)` (positive differential arm)
- `outm = Vcm - Vac * sin(M_TWO_PI * phase_q)` (negative differential arm)
- `metric = 0.9 * phase_q` (voltage-coded instantaneous wrapped phase, `0 V` to `0.9 V`)

Public parameters and legal overrides:

| Parameter | Default | Unit / range | Contract |
| --- | ---: | --- | --- |
| `Fnom` | `20.0e6` | Hz, `(0:inf)` | Frequency at zero differential input. |
| `dFdV` | `160.0e6` | Hz/V, `(-inf:inf) exclude 0.0` | Frequency shift per volt of `V(vinp, vinm)`. |
| `Fmin` | `5.0e6` | Hz, `(0:inf)` | Lower clamp for the oscillation frequency. |
| `Fmax` | `80.0e6` | Hz, `(0:inf)` | Upper clamp for the oscillation frequency. |
| `Vcm` | `0.45` | V | Common-mode output center voltage. |
| `Vac` | `0.4` | V, `(0:inf)` | Per-arm sine amplitude. |

The verification harness may exercise constant differential-control windows in
which `V(vinp)` and `V(vinm)` are held fixed, so the output is a pure
differential sine whose frequency is the clipped value of
`Fnom + dFdV * V(vinp, vinm)`. Over any such window the candidate outputs are
expected to bracket `Vcm` symmetrically — `outp = Vcm + Vac*sin(M_TWO_PI*phase_q)`
and `outm = Vcm - Vac*sin(M_TWO_PI*phase_q)` — and `metric` to track
`0.9*phase_q`, where `phase_q` is the modulo-1 phase accumulator above. The
clamp must take effect whenever the unclipped frequency would fall outside
`[Fmin, Fmax]`.

## Output

Return exactly one source artifact named `differential_vco_clip_idtmod.va`. Do
not generate a Spectre testbench for this task.
