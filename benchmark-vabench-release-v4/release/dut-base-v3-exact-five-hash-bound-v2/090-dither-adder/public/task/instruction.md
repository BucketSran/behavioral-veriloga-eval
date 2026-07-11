# Dither Adder

## Task Contract

Implement the requested Verilog-A artifact for `Dither Adder`.
- Form: `dut`
- Level: `L1`
- Category: `measurement_instrumentation_flows`
- Target artifact(s): `dither_adder.va`

Implement `dither_adder.va` in Verilog-A.

## Public Verilog-A Interface

```verilog
module dither_adder(
    input  electrical VRES_P,
    input  electrical VRES_N,
    input  electrical DPN,
    output electrical VOUT_P,
    output electrical VOUT_N
);
```

## Public Parameter Contract

| Parameter | Default | Contract |
| --- | ---: | --- |
| `DITHER_AMP` | `0.014063 V` | Nonnegative differential dither magnitude. |
| `vth` | `0.45 V` | Voltage threshold for the `DPN` polarity input. |
| `vdd` | `0.9 V` | Compatibility/supply-domain parameter retained by the module interface. |

## Required Behavior

Implement a standalone differential dither injection block. The module receives
a differential residual signal on `VRES_P/VRES_N` and a voltage-coded dither
polarity input `DPN`. When `DPN` is above the threshold, inject a positive
differential dither; when it is below the threshold, inject a negative
differential dither.

The injected differential offset is controlled by parameter `DITHER_AMP`
and must be split symmetrically between the two outputs:

```text
dither_diff = +DITHER_AMP when V(DPN) > vth
dither_diff = -DITHER_AMP when V(DPN) <= vth
VOUT_P = VRES_P + dither_diff / 2
VOUT_N = VRES_N - dither_diff / 2
```

This keeps the output common-mode equal to the input common-mode while adding
only the requested differential dither. Keep the block usable with legal
`DITHER_AMP` parameter overrides.

The standalone dither operation preserves input common-mode and does not add a
`vdd/2` output offset. Honor legal overrides of these parameters. Use `vth` to
interpret the voltage-coded `DPN` polarity input, and keep the model pure
behavioral Verilog-A. Smooth the event-updated dither target with a short
transition so the output does not introduce discontinuous digital steps. Do not
use transistor-level devices, AC/noise analysis, waveform files, validation
artifacts, or simulator side channels.

Only `dither_adder.va` is graded as the candidate implementation.

## Modeling Constraints

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The visible testbench is a public validation scenario; do not hard-code a particular stimulus table, transient stop time, or validation sample window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `dither_adder.va`. Do not include explanatory prose outside the source artifact contents.
