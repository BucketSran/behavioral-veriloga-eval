# RF Envelope Detector with Attack/Release Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `RF Envelope Detector with Attack/Release` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `rf_envelope_detector_attack_release.va`:
  - Module `rf_envelope_detector_attack_release` (entry)
    - position 0: `vin` (inout, electrical)
    - position 1: `clk` (inout, electrical)
    - position 2: `rst` (inout, electrical)
    - position 3: `enable` (inout, electrical)
    - position 4: `envelope` (inout, electrical)
    - position 5: `attack_metric` (inout, electrical)
    - position 6: `valid` (inout, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `rf_envelope_detector_attack_release` as `XDUT` with ordered public binding: vin=vin, clk=clk, rst=rst, enable=enable, envelope=envelope, attack_metric=attack_metric, valid=valid.

## Public Parameter Contract

- `rf_envelope_detector_attack_release.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `rf_envelope_detector_attack_release.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `rf_envelope_detector_attack_release.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `rf_envelope_detector_attack_release.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `rf_envelope_detector_attack_release.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `rf_envelope_detector_attack_release.attack_step` defaults to `120e-3`; valid range: finite; overrides attack_step.
- `rf_envelope_detector_attack_release.release_step` defaults to `30e-3`; valid range: finite; overrides release_step.
- `rf_envelope_detector_attack_release.tick` defaults to `250p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_RESET_OR_WHEN_DISABLED_CLEAR`: exercise and make observable: On reset or when disabled, clear envelope, metric, and `valid`. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `envelope`, `attack_metric`, `valid`.
- `P_ON_EACH_ENABLED_RISING_CLK_EDGE`: exercise and make observable: On each enabled rising `clk` edge, estimate input magnitude as distance from `vcm`. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `envelope`, `attack_metric`, `valid`.
- `P_USE_A_FASTER_ATTACK_STEP_WHEN`: exercise and make observable: Use a faster attack step when magnitude rises and a slower release step when it falls. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `envelope`, `attack_metric`, `valid`.
- `P_DRIVE_ENVELOPE_WITH_THE_TRACKED_MAGNITUDE`: exercise and make observable: Drive `envelope` with the tracked magnitude mapped into the public voltage range. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `envelope`, `attack_metric`, `valid`.
- `P_EXPOSE_WHETHER_THE_LAST_UPDATE_USED`: exercise and make observable: Expose whether the last update used attack or release on `attack_metric`. Required traces: `time`, `vin`, `clk`, `rst`, `enable`, `envelope`, `attack_metric`, `valid`.

The required trace names are: `time`, `vin`, `clk`, `rst`, `enable`, `envelope`, `attack_metric`, `valid`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
