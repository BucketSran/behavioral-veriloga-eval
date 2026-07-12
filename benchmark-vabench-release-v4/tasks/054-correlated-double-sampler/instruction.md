# Correlated Double Sampler

## Task Contract

Implement the DUT Verilog-A source file `correlated_double_sampler.va`. This is
an L1 data-converter front-end task: a two-phase correlated double sampler that
captures a reset level, captures a later signal level, and publishes the
held signal-minus-reset correction.

## Public Verilog-A Interface

Declare:

```verilog
Declare module `correlated_double_sampler` with the positional ports listed below.
```

All ports are electrical. `phi_reset` is the reset-level sample clock,
`phi_signal` is the signal-level sample clock, `vin` is the analog sampled
input, `vout` is the held corrected output, and `valid` is a voltage-coded
status output.

## Public Parameter Contract

- `vth = 0.45 V`: rising-edge threshold for `phi_reset` and `phi_signal`.
- `vcm = 0.45 V`: output common-mode level and initial/reset output level.
- `gain = 1.0`: gain applied to the signal-minus-reset difference.
- `vlo = 0.0 V`: lower clamp for `vout`.
- `vhi = 0.9 V`: upper clamp for `vout` and high level for `valid`.
- `tr = 100p`: transition rise/fall time for `vout` and `valid`.

## Required Behavior

Initialize the stored reset sample to `vcm`, drive `vout` to `vcm`, and drive
`valid` low. On each rising crossing of `phi_reset` through `vth`, sample the
current `vin` value as the reset level, drive `vout` back to `vcm`, and clear
`valid` low. On each rising crossing of `phi_signal` through `vth`, compute
`vcm + gain * (signal_level - reset_level)`, clamp that corrected value between
`vlo` and `vhi`, drive `vout` to the clamped value, and drive `valid` high to
`vhi`. Hold both outputs between sampling events.

## Modeling Constraints

Use voltage-domain Verilog-A with edge detection through `cross(...)` and
smoothed voltage contributions. Do not continuously track `vin`, ignore the
reset-level sample, reverse the sign of the subtraction, treat `phi_signal` as
the reset phase, or hard-code private waveform times from the public example harness.

## Output Contract

Return only `correlated_double_sampler.va` implementing the public module. The
file must be portable to the simulator and must not emit a example harness, private grader logic,
or explanatory prose outside the source artifact.
