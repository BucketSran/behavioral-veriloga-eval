# Phase Detector Chopper Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Phase Detector Chopper` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `phase_detector_chopper.va`:
  - Module `phase_detector_chopper` (entry)
    - position 0: `vlocal_osc` (input, electrical)
    - position 1: `vin_rf` (input, electrical)
    - position 2: `vif` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `phase_detector_chopper` as `XDUT` with ordered public binding: vlocal_osc=vlocal_osc, vin_rf=vin_rf, vif=vif.

## Public Parameter Contract

- `phase_detector_chopper.gain` defaults to `1.25`; valid range: finite; overrides gain.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_POSITIVE_LO_GAIN_PATH`: exercise and make observable: When `vlocal_osc` is positive, drive `vif = gain * vin_rf`. Required traces: `time`, `vif`, `vin_rf`, `vlocal_osc`.
- `P_NEGATIVE_LO_CHOP_PATH`: exercise and make observable: When `vlocal_osc` is not positive, drive `vif = -gain * vin_rf`. Required traces: `time`, `vif`, `vin_rf`, `vlocal_osc`.
- `P_CONTINUOUS_TRACKING`: exercise and make observable: `vif` tracks `vin_rf` and `vlocal_osc` continuously without clocked state or hidden latching. Required traces: `time`, `vif`, `vin_rf`, `vlocal_osc`.

The required trace names are: `time`, `vif`, `vin_rf`, `vlocal_osc`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
