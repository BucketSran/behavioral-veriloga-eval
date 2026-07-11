# Vargain Diffamp Clip

## Task Contract

Implement `vargain_diffamp_clip.va` as a parameterized voltage-controlled differential gain block with output clipping.

## Public Verilog-A Interface

Use this module signature:

```verilog
module vargain_diffamp_clip(sigin_p, sigin_n, sigctrl_p, sigctrl_n, sigout);
```

All ports are scalar `electrical` nodes. `sigin_p`/`sigin_n` are the differential signal input, `sigctrl_p`/`sigctrl_n` are the differential gain-control input, and `sigout` is the clipped output.

## Public Parameter Contract

- `gain_const`: gain multiplier, default `3.0`.
- `sigout_high`: upper clipping limit, default `1.0`.
- `sigout_low`: lower clipping limit, default `-1.0`.
- `sigin_offset`: offset subtracted from the differential signal input before gain, default `0.05`.

## Required Behavior

- Compute the differential signal as `V(sigin_p, sigin_n)`.
- Compute the differential control as `V(sigctrl_p, sigctrl_n)`.
- Subtract `sigin_offset` from the differential signal.
- Multiply the offset-corrected signal by the differential control and `gain_const`.
- Clamp the result to the public output limits.
- Drive `sigout` with the clipped target.

## Modeling Constraints

Use a single voltage contribution for `sigout`. Do not use current contributions, transistor devices, filtering, checker logic, out-of-band test hooks, or testbench-specific constants.

## Output Contract

Return exactly one source artifact named `vargain_diffamp_clip.va`.
