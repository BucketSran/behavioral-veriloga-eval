# Differential VCO With Clip And Idtmod Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `differential_vco_clip_idtmod.va`:
  - Module `differential_vco_clip_idtmod` (entry)
    - position 0: `vinp` (input, electrical)
    - position 1: `vinm` (input, electrical)
    - position 2: `outp` (output, electrical)
    - position 3: `outm` (output, electrical)
    - position 4: `metric` (output, electrical)

## Public Parameter Contract

- `differential_vco_clip_idtmod.Fnom` defaults to `20.0e6 from (0:inf)`; valid range: finite; overrides Fnom.
- `differential_vco_clip_idtmod.dFdV` defaults to `160.0e6 exclude 0.0`; valid range: finite; overrides dFdV.
- `differential_vco_clip_idtmod.Fmin` defaults to `5.0e6 from (0:inf)`; valid range: finite; overrides Fmin.
- `differential_vco_clip_idtmod.Fmax` defaults to `80.0e6 from (0:inf)`; valid range: finite; overrides Fmax.
- `differential_vco_clip_idtmod.Vcm` defaults to `0.45`; valid range: finite; overrides Vcm.
- `differential_vco_clip_idtmod.Vac` defaults to `0.4 from (0:inf)`; valid range: finite; overrides Vac.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_FREQ_Q_CLIP_FNOM_DFDV_V`: restore: `freq_q = `clip(Fnom + dFdV * V(vinp, vinm), Fmin, Fmax)` Required traces: `time`, `vinp`, `vinm`, `outp`, `outm`, `metric`.
- `P_PHASE_Q_IDTMOD_FREQ_Q_0`: restore: `phase_q = idtmod(freq_q, 0.0, 1.0)` (modulo-1 phase accumulator) Required traces: `time`, `vinp`, `vinm`, `outp`, `outm`, `metric`.
- `P_OUTP_VCM_VAC_SIN_M_TWO`: restore: `outp = Vcm + Vac * sin(M_TWO_PI * phase_q)` (positive differential arm) Required traces: `time`, `vinp`, `vinm`, `outp`, `outm`, `metric`.
- `P_OUTM_VCM_VAC_SIN_M_TWO`: restore: `outm = Vcm - Vac * sin(M_TWO_PI * phase_q)` (negative differential arm) Required traces: `time`, `vinp`, `vinm`, `outp`, `outm`, `metric`.
- `P_METRIC_0_9_PHASE_Q_VOLTAGE`: restore: `metric = 0.9 * phase_q` (voltage-coded instantaneous wrapped phase, `0 V` to `0.9 V`) Required traces: `time`, `vinp`, `vinm`, `outp`, `outm`, `metric`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `differential_vco_clip_idtmod.va`.
Every supplied `.va` file is editable; do not add or omit files.
