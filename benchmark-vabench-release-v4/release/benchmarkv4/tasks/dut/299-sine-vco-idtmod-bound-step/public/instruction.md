# Sine VCO With Idtmod And Bound Step

## Task Contract

Implement one behavioral Verilog-A DUT file named `sine_vco_idtmod_bound_step.va`.

This is a PLL clock-and-timing task following the common behavioral VCO pattern
of integrating instantaneous frequency into wrapped phase and driving a sine
output. Keep the model pure voltage-domain behavioral Verilog-A: do not
instantiate transistor-level devices and do not use current-domain `I(...)`
branch contributions.

## Public Verilog-A Interface

```verilog
module sine_vco_idtmod_bound_step (
    input  electrical vin,
    output electrical out,
    output electrical metric
);
```

## Public Parameter Contract

Public parameters and legal overrides:

| Parameter | Default | Unit / range | Contract |
| --- | ---: | --- | --- |
| `center_freq` | `20.0e6` | Hz, `(0:inf)` | Output frequency at `V(vin) = 0`. |
| `vco_gain` | `40.0e6` | Hz/V, `(-inf:inf) exclude 0.0` | Frequency shift per volt of `V(vin)`. |
| `vco_amp` | `0.9` | V, `(0:inf)` | Sine and metric peak amplitude. |
| `vco_ppc` | `40` | integer, `[4:inf)` | Minimum points per output cycle enforced via `$bound_step`. |

Valid operating points keep `freq_q > 0` so the requested `$bound_step` interval
is positive. The supplied verification scenarios hold `V(vin)` constant over
each measurement window, so the output should be a pure sine whose frequency is
set by `center_freq + vco_gain * V(vin)`.

## Required Behavior

Use `idtmod()` as a voltage-domain phase integrator whose instantaneous
frequency is controlled by `vin`, and produce a continuous-time sine output.

This is a behavioral continuous-time task, not a conservative-current/KCL task.
Do not use `I(...)`, `ddt(...)`, or `idt(...)`.

Implement:

- `freq_q = center_freq + vco_gain * V(vin)`
- `phase_q = idtmod(freq_q, 0.0, 1.0)` (modulo-1 phase accumulator)
- `out = vco_amp * sin(M_TWO_PI * phase_q)` (bipolar sine centered at `0 V`)
- `metric = vco_amp * phase_q` (voltage-coded instantaneous wrapped phase, `0 V` to `vco_amp`)
- call `$bound_step(1.0 / (vco_ppc * freq_q))` every step so the sine is resolved
  with at least `vco_ppc` timepoints per cycle

## Modeling Constraints

This is a PLL clock-and-timing task following the common behavioral VCO pattern
of integrating instantaneous frequency into wrapped phase and driving a sine
output. Keep the model pure voltage-domain behavioral Verilog-A: do not
instantiate transistor-level devices and do not use current-domain `I(...)`
branch contributions.

Keep the implementation behavioral and public-interface compatible. Do not add Spectre testbench code, simulator-specific hooks, or extra output artifacts.

## Output Contract

Return exactly one source artifact named `sine_vco_idtmod_bound_step.va`. Do not
generate a testbench for this task.
