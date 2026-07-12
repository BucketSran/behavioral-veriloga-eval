# Acquisition Limited Sample And Hold Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Acquisition Limited Sample And Hold` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `acquisition_limited_sample_hold.va`:
  - Module `acquisition_limited_sample_hold` (entry)
    - position 0: `sample` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `vout` (output, electrical)
    - position 4: `metric` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `acquisition_limited_sample_hold` as `XDUT` with ordered public binding: sample=sample, rst=rst, vin=vin, vout=vout, metric=metric.

## Public Parameter Contract

- `acquisition_limited_sample_hold.vth` defaults to `0.45` V; valid range: vth > 0; sets the sample and reset logic threshold.
- `acquisition_limited_sample_hold.vinit` defaults to `0.45` V; valid range: any finite voltage; sets the initial and reset held-output voltage.
- `acquisition_limited_sample_hold.alpha` defaults to `0.42`; valid range: 0 < alpha <= 1; sets the fraction of the remaining vin-to-vout error acquired per update.
- `acquisition_limited_sample_hold.tick` defaults to `1e-09` s; valid range: tick > 0; sets the interval between acquisition updates while sample is high.
- `acquisition_limited_sample_hold.tr` defaults to `2e-10` s; valid range: tr > 0; sets vout and metric transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET`: exercise and make observable: While rst is above vth, vout returns to vinit and metric is low. Required traces: `time`, `rst`, `vout`, `metric`.
- `P_ACQUISITION_ENABLE`: exercise and make observable: When sample is above vth and reset is inactive, metric is high and vout is allowed to acquire vin. Required traces: `time`, `sample`, `rst`, `vin`, `vout`, `metric`.
- `P_FINITE_ACQUISITION`: exercise and make observable: At each tick during acquisition, vout advances by alpha times the remaining difference from the current vin rather than jumping instantaneously. Required traces: `time`, `sample`, `vin`, `vout`.
- `P_ACQUISITION_CONVERGENCE`: exercise and make observable: For a constant vin and repeated acquisition updates, vout moves monotonically toward vin without overshoot for the declared alpha range. Required traces: `time`, `sample`, `vin`, `vout`.
- `P_HOLD`: exercise and make observable: A falling sample crossing freezes the last acquired value; vout holds it and metric remains low until acquisition resumes or reset is asserted. Required traces: `time`, `sample`, `rst`, `vin`, `vout`, `metric`.

The required trace names are: `time`, `sample`, `rst`, `vin`, `vout`, `metric`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
