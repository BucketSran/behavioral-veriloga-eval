# PFD Up Down State Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `PFD Up Down State` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `pfd_up_down_state.va`:
  - Module `pfd_up_down_state` (entry)
    - position 0: `ref` (input, electrical)
    - position 1: `fb` (input, electrical)
    - position 2: `up` (output, electrical)
    - position 3: `down` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `pfd_up_down_state` as `XDUT` with ordered public binding: ref=ref, fb=fb, up=up, down=down.

## Public Parameter Contract

- `pfd_up_down_state.vdd` defaults to `1.2`; valid range: finite; overrides vdd.
- `pfd_up_down_state.tdel` defaults to `10p`; valid range: finite; overrides tdel.
- `pfd_up_down_state.tr` defaults to `10p`; valid range: finite; overrides tr.
- `pfd_up_down_state.tf` defaults to `10p`; valid range: finite; overrides tf.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_DETECT_RISING_REF_AND_FB_CROSSINGS`: exercise and make observable: Detect rising `ref` and `fb` crossings at `vdd/2`. Required traces: `time`, `down`, `fb`, `ref`, `up`.
- `P_MAINTAIN_AN_INTEGER_DETECTOR_STATE_BOUNDED`: exercise and make observable: Maintain an integer detector state bounded to `-1`, `0`, or `+1`. Required traces: `time`, `down`, `fb`, `ref`, `up`.
- `P_A_RISING_REF_EDGE_INCREMENTS_THE`: exercise and make observable: A rising `ref` edge increments the state up to `+1`. Required traces: `time`, `down`, `fb`, `ref`, `up`.
- `P_A_RISING_FB_EDGE_DECREMENTS_THE`: exercise and make observable: A rising `fb` edge decrements the state down to `-1`. Required traces: `time`, `down`, `fb`, `ref`, `up`.
- `P_DRIVE_UP_HIGH_WHEN_THE_STATE`: exercise and make observable: Drive `up` high when the state is `+1`. Required traces: `time`, `down`, `fb`, `ref`, `up`.
- `P_DRIVE_DOWN_HIGH_WHEN_THE_STATE`: exercise and make observable: Drive `down` high when the state is `-1`. Required traces: `time`, `down`, `fb`, `ref`, `up`.

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
