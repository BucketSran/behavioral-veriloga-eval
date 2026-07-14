# Dither Noise Like Deterministic Source Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Dither Noise Like Deterministic Source` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `noise_gen_ref.va`:
  - Module `noise_gen` (entry)
    - position 0: `vin_i` (input, electrical)
    - position 1: `vout_o` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `noise_gen` as `XDUT` with ordered public binding: vin_i=vin_i, vout_o=vout_o.

## Public Parameter Contract

- `noise_gen.sigma` defaults to `0.01` V; valid range: sigma >= 0; scales the held deterministic perturbation added to vin_i.
- `noise_gen.dt` defaults to `5e-10` s; valid range: dt > 0; sets the periodic interval between perturbation-sample updates.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_PERIODIC_UPDATE`: exercise and make observable: The deterministic perturbation sample updates once every dt seconds. Required traces: `time`, `vin_i`, `vout_o`.
- `P_SAMPLE_HOLD`: exercise and make observable: Between update events, the perturbation vout_o minus vin_i remains piecewise constant. Required traces: `time`, `vin_i`, `vout_o`.
- `P_ADDITIVE_OUTPUT`: exercise and make observable: At all times after the first update, vout_o equals vin_i plus sigma times the currently held normalized perturbation sample. Required traces: `time`, `vin_i`, `vout_o`.
- `P_DETERMINISTIC_SEQUENCE`: exercise and make observable: The normalized perturbation sample repeats the public eight-sample sequence [-1.0, -0.5, 0.0, 0.5, 1.0, 0.5, 0.0, -0.5], advancing by one entry at each dt update. Required traces: `time`, `vin_i`, `vout_o`.
- `P_ZERO_MEAN_DITHER`: exercise and make observable: Every complete eight-sample sequence period is exactly zero mean, and every perturbation is bounded within [-sigma, +sigma]. Required traces: `time`, `vin_i`, `vout_o`.

The required trace names are: `time`, `vin_i`, `vout_o`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
