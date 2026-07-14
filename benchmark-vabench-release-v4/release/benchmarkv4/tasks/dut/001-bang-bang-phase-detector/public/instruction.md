# Bang-Bang Phase Detector

## Task Contract

Implement one Verilog-A DUT artifact for a bang-bang phase detector used in a clock/data recovery loop.

- Target artifact: `bbpd_ref.va`

The model compares the sampled relationship between incoming data, clock, and retimed data, then emits short voltage-coded correction pulses on `up` or `down`.

## Public Verilog-A Interface

The file must define module `bbpd_ref` with this exact positional port order:

```verilog
module bbpd_ref (
    input  electrical data,
    input  electrical clk,
    input  electrical retimed_data,
    output electrical up,
    output electrical down
);
```

Use voltage-domain `electrical` ports.

## Public Parameter Contract

Provide these overrideable public parameters:

- `vdd = 0.9 V`: voltage-coded logic high level for `up` and `down`.
- `vth = 0.45 V`: logic threshold for `data`, `clk`, and `retimed_data`.
- `trf = 10 ps`: rise/fall smoothing time for correction pulses.
- `td = 0 ps`: output transition delay.

## Required Behavior

Treat logic low as below `vth` and logic high as above `vth`.

On each rising or falling transition of `data`:

- assert `up` when `clk` is high and `retimed_data` is low;
- assert `down` when `clk` is low and `retimed_data` is high;
- assert neither output when the observed relationship does not indicate a correction direction;
- never drive `up` and `down` high at the same time.

Each correction output is a pulse near `vdd` that returns to 0 V after the next clock transition. Use smooth voltage-domain output contributions.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A. Keep event-triggered state updates separate from unconditional output contributions. Do not add extra ports, files, debug outputs, pass/fail flags, or state observables that are not part of the public interface.

## Output Contract

Return exactly one complete source artifact named `bbpd_ref.va`.
