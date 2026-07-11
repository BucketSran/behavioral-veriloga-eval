# VCO Phase Integrator

## Task Contract

Implement one Verilog-A DUT artifact for a voltage-controlled oscillator phase accumulator.

- Target artifact: `vco_phase_integrator.va`

The model exposes both wrapped phase and a voltage-coded clock.

## Public Verilog-A Interface

Declare module `vco_phase_integrator` with this exact positional port order:

```verilog
module vco_phase_integrator(
    input  electrical vctrl,
    output electrical phase,
    output electrical clk
);
```

## Public Parameter Contract

Provide this overrideable public parameter:

- `tr = 200 ps`: rise/fall smoothing time for `phase` and `clk`.

## Required Behavior

- Maintain a real phase state normalized to the range `[0, 1)`.
- Update the phase state on a periodic `1 ns` timer.
- At each update, increment phase by `0.03 + 0.09 * V(vctrl)`.
- When the phase reaches or exceeds `1.0`, wrap it by one cycle and toggle `clk`.
- Drive `phase` as the wrapped normalized phase voltage.
- Drive `clk` as a smoothed `0 V` / `0.9 V` voltage-coded clock.
- The clock edge rate must increase when `vctrl` increases.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A. Use voltage contributions only; do not use current contributions, `ddt()`, `idt()`, transistor-level devices, AC/noise analysis, or topology-level assumptions. Do not add extra ports, files, debug outputs, pass/fail flags, or state observables that are not part of the public interface.

## Output Contract

Return exactly one complete source artifact named `vco_phase_integrator.va`.
