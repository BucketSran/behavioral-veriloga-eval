# Dither Noise Like Deterministic Source Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `noise_gen_ref.va`:
  - Module `noise_gen` (entry)
    - position 0: `vin_i` (input, electrical)
    - position 1: `vout_o` (output, electrical)

## Public Parameter Contract

- `noise_gen.sigma` defaults to `0.01` V; valid range: sigma >= 0; scales the held deterministic perturbation added to vin_i.
- `noise_gen.dt` defaults to `5e-10` s; valid range: dt > 0; sets the periodic interval between perturbation-sample updates.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_PERIODIC_UPDATE`: restore: The deterministic perturbation sample updates once every dt seconds. Required traces: `time`, `vin_i`, `vout_o`.
- `P_SAMPLE_HOLD`: restore: Between update events, the perturbation vout_o minus vin_i remains piecewise constant. Required traces: `time`, `vin_i`, `vout_o`.
- `P_ADDITIVE_OUTPUT`: restore: At all times after the first update, vout_o equals vin_i plus sigma times the currently held normalized perturbation sample. Required traces: `time`, `vin_i`, `vout_o`.
- `P_DETERMINISTIC_SEQUENCE`: restore: The normalized perturbation sample repeats the public eight-sample sequence [-1.0, -0.5, 0.0, 0.5, 1.0, 0.5, 0.0, -0.5], advancing by one entry at each dt update. Required traces: `time`, `vin_i`, `vout_o`.
- `P_ZERO_MEAN_DITHER`: restore: Every complete eight-sample sequence period is exactly zero mean, and every perturbation is bounded within [-sigma, +sigma]. Required traces: `time`, `vin_i`, `vout_o`.

## Modeling Constraints

- Use deterministic periodic sample-and-hold updates rather than physical noise analysis or random simulator state.
- Apply sigma only as a perturbation scale and preserve the continuously observed vin_i contribution.
- Do not add undeclared seed inputs, files, ports, or validation-only sequence branches.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `noise_gen_ref.va`.
Every supplied `.va` file is editable; do not add or omit files.
