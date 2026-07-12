# XOR Phase Detector Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `XOR Phase Detector` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `xor_phase_detector.va`:
  - Module `xor_phase_detector` (entry)
    - position 0: `ref` (input, electrical)
    - position 1: `fb` (input, electrical)
    - position 2: `up` (output, electrical)
    - position 3: `down` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `xor_phase_detector` as `XDUT` with ordered public binding: ref=ref, fb=fb, up=up, down=down.

## Public Parameter Contract

- `xor_phase_detector.vdd` defaults to `1.2`; valid range: finite; overrides vdd.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_INTERPRET_REF_AND_FB_LOGIC_LEVELS`: exercise and make observable: Interpret `ref` and `fb` logic levels using a threshold of `vdd/2`. Required traces: `time`, `down`, `fb`, `ref`, `up`.
- `P_DRIVE_UP_HIGH_WHEN_THE_INTERPRETED`: exercise and make observable: Drive `up` high when the interpreted `ref` and `fb` levels differ. Required traces: `time`, `down`, `fb`, `ref`, `up`.
- `P_DRIVE_DOWN_HIGH_WHEN_THE_INTERPRETED`: exercise and make observable: Drive `down` high when the interpreted `ref` and `fb` levels match. Required traces: `time`, `down`, `fb`, `ref`, `up`.
- `P_UPDATE_OUTPUTS_COMBINATIONALLY_FROM_THE_CURREN`: exercise and make observable: Update outputs combinationally from the current input voltages. Required traces: `time`, `down`, `fb`, `ref`, `up`.

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
