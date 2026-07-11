# Clocked Sine Source

## Task Contract

Implement the requested Verilog-A artifact for `Clocked Sine Source`.
- Form: `dut`
- Level: `L2`
- Category: `measurement_instrumentation_flows`
- Target artifact(s): `vin_src.va`
- Public support artifact(s): `lfsr.va`, `dither_adder.va`, `gain_amp_fixed.va`

Implement `vin_src.va` in Verilog-A.

## Public Verilog-A Interface

```verilog
module vin_src(
    input  electrical CLK,
    input  electrical RST_N,
    output electrical VOUT_P,
    output electrical VOUT_N
);
```

## Public Parameter Contract

The public parameters declared by the target artifact are part of the contract and may be overridden by validation harnesses. Preserve their names, defaults, ranges, and meanings:

- `parameter real vdd = 0.9;` in `vin_src.va`.
- `parameter real vth = 0.45;` in `vin_src.va`.
- `parameter real ampl = 0.15;` in `vin_src.va`.
- `parameter real freq = 300e3;` in `vin_src.va`.
- `parameter real sigma = 0.01;` in `vin_src.va`.
- `parameter integer SEED = 0;` in `vin_src.va`.

## Required Behavior

This is an L2 measurement-flow stimulus macro, retained as an independent DUT
because it provides the clocked differential source used by composed gain and
linearity measurement flows. Implement `vin_src.va`, a clocked differential
sine stimulus source that can support composed measurement flows such as
gain-extraction benches.

On each rising crossing of `CLK`, if `RST_N` is high, update `VOUT_P` to a
sampled sine value around `vdd/2`. Keep `VOUT_N` at `vdd/2` as the reference
side. While reset is low, hold both outputs near `vdd/2`.

```text
VOUT_P = vdd/2 + ampl*sin(2*pi*freq*t) + optional deterministic perturbation
VOUT_N = vdd/2
```

Use the public parameters `vdd`, `vth`, `ampl`, `freq`, `sigma`, and `SEED`
where applicable. The important behavioral boundary is that the source is
clocked/sample-held rather than continuously recomputing random values at every
analog evaluation point.

Public parameters:

- `vdd = 0.9 V`: positive output common-mode supply parameter.
- `vth = 0.45 V`: voltage threshold for `CLK` and `RST_N`.
- `ampl = 0.15 V`: sine amplitude before any testbench override.
- `freq = 300 kHz`: sine frequency before any testbench override.
- `sigma = 0.01 V`: deterministic random perturbation scale.
- `SEED = 0`: seed passed to `$rdist_normal(SEED, 0, 1)`.

Sample the sine and random perturbation only on rising `CLK` crossings after
reset release. `VOUT_N` should remain at `vdd/2`; the perturbation is applied
to the positive side so the composed measurement flow sees a repeatable
single-ended stimulus component.

Use `vth` with a default near 0.45 V to interpret the voltage-coded `CLK` and
`RST_N` control inputs, and keep the model pure behavioral Verilog-A. Do not use
transistor-level devices, AC/noise analysis, waveform files, validation artifacts,
or simulator side channels.

Only `vin_src.va` is the source macro under review. The public harness supplies
`lfsr.va`, `dither_adder.va`, and `gain_amp_fixed.va` for composed-flow
evaluation; do not return or redefine those support modules.

## Modeling Constraints

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The visible testbench is a public validation scenario; do not hard-code a particular stimulus table, transient stop time, or validation sample window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `vin_src.va`. Do not include explanatory prose outside the source artifact contents.
