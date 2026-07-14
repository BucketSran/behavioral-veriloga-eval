# Differential VCO With Clip And Idtmod Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Differential VCO With Clip And Idtmod` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `differential_vco_clip_idtmod.va`:
  - Module `differential_vco_clip_idtmod` (entry)
    - position 0: `vinp` (input, electrical)
    - position 1: `vinm` (input, electrical)
    - position 2: `outp` (output, electrical)
    - position 3: `outm` (output, electrical)
    - position 4: `metric` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `differential_vco_clip_idtmod` as `XDUT` with ordered public binding: vinp=vinp, vinm=vinm, outp=outp, outm=outm, metric=metric.

## Public Parameter Contract

- `differential_vco_clip_idtmod.Fnom` defaults to `20.0e6 from (0:inf)`; valid range: finite; overrides Fnom.
- `differential_vco_clip_idtmod.dFdV` defaults to `160.0e6 exclude 0.0`; valid range: finite; overrides dFdV.
- `differential_vco_clip_idtmod.Fmin` defaults to `5.0e6 from (0:inf)`; valid range: finite; overrides Fmin.
- `differential_vco_clip_idtmod.Fmax` defaults to `80.0e6 from (0:inf)`; valid range: finite; overrides Fmax.
- `differential_vco_clip_idtmod.Vcm` defaults to `0.45`; valid range: finite; overrides Vcm.
- `differential_vco_clip_idtmod.Vac` defaults to `0.4 from (0:inf)`; valid range: finite; overrides Vac.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_FREQ_Q_CLIP_FNOM_DFDV_V`: exercise and make observable: `freq_q = `clip(Fnom + dFdV * V(vinp, vinm), Fmin, Fmax)` Required traces: `time`, `vinp`, `vinm`, `outp`, `outm`, `metric`.
- `P_PHASE_Q_IDTMOD_FREQ_Q_0`: exercise and make observable: `phase_q = idtmod(freq_q, 0.0, 1.0)` (modulo-1 phase accumulator) Required traces: `time`, `vinp`, `vinm`, `outp`, `outm`, `metric`.
- `P_OUTP_VCM_VAC_SIN_M_TWO`: exercise and make observable: `outp = Vcm + Vac * sin(M_TWO_PI * phase_q)` (positive differential arm) Required traces: `time`, `vinp`, `vinm`, `outp`, `outm`, `metric`.
- `P_OUTM_VCM_VAC_SIN_M_TWO`: exercise and make observable: `outm = Vcm - Vac * sin(M_TWO_PI * phase_q)` (negative differential arm) Required traces: `time`, `vinp`, `vinm`, `outp`, `outm`, `metric`.
- `P_METRIC_0_9_PHASE_Q_VOLTAGE`: exercise and make observable: `metric = 0.9 * phase_q` (voltage-coded instantaneous wrapped phase, `0 V` to `0.9 V`) Required traces: `time`, `vinp`, `vinm`, `outp`, `outm`, `metric`.

The required trace names are: `time`, `vinp`, `vinm`, `outp`, `outm`, `metric`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
