# Sine VCO With Idtmod And Bound Step Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `sine_vco_idtmod_bound_step.va`:
  - Module `sine_vco_idtmod_bound_step` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `out` (output, electrical)
    - position 2: `metric` (output, electrical)

## Public Parameter Contract

- `sine_vco_idtmod_bound_step.center_freq` defaults to `20.0e6 from (0:inf)`; valid range: finite; overrides center_freq.
- `sine_vco_idtmod_bound_step.vco_gain` defaults to `40.0e6 exclude 0.0`; valid range: finite; overrides vco_gain.
- `sine_vco_idtmod_bound_step.vco_amp` defaults to `0.9 from (0:inf)`; valid range: finite; overrides vco_amp.
- `sine_vco_idtmod_bound_step.vco_ppc` defaults to `40 from [4:inf)`; valid range: finite; overrides vco_ppc.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_FREQ_Q_CENTER_FREQ_VCO_GAIN`: restore: `freq_q = center_freq + vco_gain * V(vin)` Required traces: `time`, `vin`, `out`, `metric`.
- `P_PHASE_Q_IDTMOD_FREQ_Q_0`: restore: `phase_q = idtmod(freq_q, 0.0, 1.0)` (modulo-1 phase accumulator) Required traces: `time`, `vin`, `out`, `metric`.
- `P_OUT_VCO_AMP_SIN_M_TWO`: restore: `out = vco_amp * sin(M_TWO_PI * phase_q)` (bipolar sine centered at `0 V`) Required traces: `time`, `vin`, `out`, `metric`.
- `P_METRIC_VCO_AMP_PHASE_Q_VOLTAGE`: restore: `metric = vco_amp * phase_q` (voltage-coded instantaneous wrapped phase, `0 V` to `vco_amp`) Required traces: `time`, `vin`, `out`, `metric`.
- `P_CALL_BOUND_STEP_1_0_VCO`: restore: call `$bound_step(1.0 / (vco_ppc * freq_q))` every step so the sine is resolved Required traces: `time`, `vin`, `out`, `metric`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `sine_vco_idtmod_bound_step.va`.
Every supplied `.va` file is editable; do not add or omit files.
