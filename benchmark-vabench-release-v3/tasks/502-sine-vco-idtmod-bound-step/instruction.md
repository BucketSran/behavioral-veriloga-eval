# Sine VCO With Idtmod And Bound Step

Implement one behavioral Verilog-A DUT file named `sine_vco_idtmod_bound_step.va`.

This is a PLL clock-and-timing task recast from the Cadence `VCO1.va` example
(`BehavModelVAMS_M08_Operation/.solutions/VCO1.va`). Keep the model pure
voltage-domain behavioral Verilog-A: do not instantiate transistor-level
devices and do not use current-domain `I(...)` branch contributions.

## Interface

```verilog
module sine_vco_idtmod_bound_step (
    input  electrical vin,
    output electrical out,
    output electrical metric
);
```

## Required Behavior

Use `idtmod()` as a voltage-domain phase integrator whose instantaneous
frequency is controlled by `vin`, and produce a continuous-time sine output.

This is a behavioral continuous-time task, not a conservative-current/KCL task.
Do not use `I(...)`, `ddt(...)`, or `idt(...)`.

Use voltage-coded logic levels with high outputs near `0.9 V` and low outputs
near `0.0 V`, threshold `vth = 0.45 V`.

Implement:

- `freq_q = center_freq + vco_gain * V(vin)`
- `phase_q = idtmod(freq_q, 0.0, 1.0)` (modulo-1 phase accumulator)
- `out = vco_amp * sin(M_TWO_PI * phase_q)` (unipolar sine, ranges `0 V` to `vco_amp`)
- `metric = vco_amp * phase_q` (voltage-coded instantaneous wrapped phase, `0 V` to `vco_amp`)
- call `$bound_step(1.0 / (vco_ppc * freq_q))` every step so the sine is resolved
  with at least `vco_ppc` timepoints per cycle

Public parameters and legal overrides:

| Parameter | Default | Unit / range | Contract |
| --- | ---: | --- | --- |
| `center_freq` | `20.0e6` | Hz, `(0:inf)` | Output frequency at `V(vin) = 0`. |
| `vco_gain` | `40.0e6` | Hz/V, `(-inf:inf) exclude 0.0` | Frequency shift per volt of `V(vin)`. |
| `vco_amp` | `0.9` | V, `(0:inf)` | Sine and metric peak amplitude. |
| `vco_ppc` | `40` | integer, `[4:inf)` | Minimum points per output cycle enforced via `$bound_step`. |

The verification harness may exercise constant-control measurement windows in
which `V(vin)` is held fixed, so the output is a pure sine whose frequency is
set by `center_freq + vco_gain * V(vin)`. Over any such window the candidate
output is expected to track `vco_amp * sin(M_TWO_PI * phase_q)` and `metric` to
track `vco_amp * phase_q`, where `phase_q` is the modulo-1 phase accumulator
above.

## Output

Return exactly one source artifact named `sine_vco_idtmod_bound_step.va`. Do not
generate a Spectre testbench for this task.
