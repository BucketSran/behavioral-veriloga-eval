# Vargain Diffamp Clip Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `vargain_diffamp_clip.va`:
  - Module `vargain_diffamp_clip` (entry)
    - position 0: `sigin_p` (input, electrical)
    - position 1: `sigin_n` (input, electrical)
    - position 2: `sigctrl_p` (input, electrical)
    - position 3: `sigctrl_n` (input, electrical)
    - position 4: `sigout` (output, electrical)

## Public Parameter Contract

- `vargain_diffamp_clip.gain_const` defaults to `3.0`; valid range: finite; overrides gain_const.
- `vargain_diffamp_clip.sigout_high` defaults to `1.0`; valid range: finite; overrides sigout_high.
- `vargain_diffamp_clip.sigout_low` defaults to `-1.0`; valid range: finite; overrides sigout_low.
- `vargain_diffamp_clip.sigin_offset` defaults to `0.05`; valid range: finite; overrides sigin_offset.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_COMPUTE_THE_DIFFERENTIAL_SIGNAL_AS_V`: restore: Compute the observable input signal as `V(sigin_p, sigin_n)`. Required traces: `time`, `sigctrl_n`, `sigctrl_p`, `sigin_n`, `sigin_p`, `sigout`.
- `P_COMPUTE_THE_DIFFERENTIAL_CONTROL_AS_V`: restore: Compute the gain-control term as `V(sigctrl_p, sigctrl_n)` with the documented polarity. Required traces: `time`, `sigctrl_n`, `sigctrl_p`, `sigin_n`, `sigin_p`, `sigout`.
- `P_SUBTRACT_SIGIN_OFFSET_FROM_THE_DIFFERENTIAL`: restore: Subtract `sigin_offset` from the differential input before gain multiplication. Required traces: `time`, `sigctrl_n`, `sigctrl_p`, `sigin_n`, `sigin_p`, `sigout`.
- `P_MULTIPLY_THE_OFFSET_CORRECTED_SIGNAL_BY`: restore: Multiply the offset-corrected signal by the differential control and `gain_const`. Required traces: `time`, `sigctrl_n`, `sigctrl_p`, `sigin_n`, `sigin_p`, `sigout`.
- `P_CLAMP_THE_RESULT_TO_THE_PUBLIC`: restore: Clamp the amplified target to the public positive and negative output limits. Required traces: `time`, `sigctrl_n`, `sigctrl_p`, `sigin_n`, `sigin_p`, `sigout`.
- `P_DRIVE_SIGOUT_WITH_THE_CLIPPED_TARGET`: restore: Drive `sigout` with the clipped target transfer and correct output scale. Required traces: `time`, `sigctrl_n`, `sigctrl_p`, `sigin_n`, `sigin_p`, `sigout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `vargain_diffamp_clip.va`.
Every supplied `.va` file is editable; do not add or omit files.
