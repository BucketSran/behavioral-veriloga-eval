# RS Phase Detector Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `RS Phase Detector` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `rs_phase_detector.va`:
  - Module `rs_phase_detector` (entry)
    - position 0: `ref` (input, electrical)
    - position 1: `fb` (input, electrical)
    - position 2: `up` (output, electrical)
    - position 3: `down` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `rs_phase_detector` as `XDUT` with ordered public binding: ref=ref, fb=fb, up=up, down=down.

## Public Parameter Contract

- `rs_phase_detector.vdd` defaults to `1.2`; valid range: finite; overrides vdd.
- `rs_phase_detector.tdel` defaults to `10p`; valid range: finite; overrides tdel.
- `rs_phase_detector.tr` defaults to `10p`; valid range: finite; overrides tr.
- `rs_phase_detector.tf` defaults to `10p`; valid range: finite; overrides tf.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_DETECT_RISING_REF_AND_FB_CROSSINGS`: exercise and make observable: Detect rising `ref` and `fb` crossings at `vdd/2`. Required traces: `time`, `down`, `fb`, `ref`, `up`.
- `P_A_RISING_REF_EDGE_SETS_THE`: exercise and make observable: A rising `ref` edge sets the latch state so `up` is high and `down` is low. Required traces: `time`, `down`, `fb`, `ref`, `up`.
- `P_A_RISING_FB_EDGE_RESETS_THE`: exercise and make observable: A rising `fb` edge resets the latch state so `up` is low and `down` is high. Required traces: `time`, `down`, `fb`, `ref`, `up`.
- `P_HOLD_THE_MOST_RECENT_LATCH_STATE`: exercise and make observable: Hold the most recent latch state between qualifying input edges. Required traces: `time`, `down`, `fb`, `ref`, `up`.
- `P_INITIALIZE_TO_THE_RESET_STATE_WITH`: exercise and make observable: Initialize to the reset state with `up` low and `down` high. Required traces: `time`, `down`, `fb`, `ref`, `up`.

The required trace names are: `time`, `down`, `fb`, `ref`, `up`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
