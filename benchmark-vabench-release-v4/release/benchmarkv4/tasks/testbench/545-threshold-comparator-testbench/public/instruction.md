# Threshold Comparator Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Threshold Comparator` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `comparator.va`:
  - Module `comparator` (entry)
    - position 0: `VDD` (inout, electrical)
    - position 1: `VSS` (inout, electrical)
    - position 2: `VINP` (input, electrical)
    - position 3: `VINN` (input, electrical)
    - position 4: `OUT_P` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `comparator` as `XDUT` with ordered public binding: VDD=VDD, VSS=VSS, VINP=VINP, VINN=VINN, OUT_P=OUT_P.

## Public Parameter Contract

- `comparator.tedge` defaults to `1e-10` s; valid range: tedge > 0; sets OUT_P rail-transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_INITIAL_DECISION`: exercise and make observable: At initialization, OUT_P reflects the sign of VINP minus VINN. Required traces: `time`, `VINP`, `VINN`, `OUT_P`.
- `P_RISING_DIFFERENTIAL`: exercise and make observable: When VINP crosses above VINN, OUT_P transitions to the VDD rail. Required traces: `time`, `VDD`, `VINP`, `VINN`, `OUT_P`.
- `P_FALLING_DIFFERENTIAL`: exercise and make observable: When VINP crosses below VINN, OUT_P transitions to the VSS rail. Required traces: `time`, `VSS`, `VINP`, `VINN`, `OUT_P`.
- `P_BIDIRECTIONAL_RESPONSE`: exercise and make observable: Repeated differential crossings in either direction update the retained decision without requiring a clock or reset. Required traces: `time`, `VINP`, `VINN`, `OUT_P`.
- `P_RAIL_SMOOTHING`: exercise and make observable: OUT_P is rail-referenced and changes with finite transition smoothing set by tedge. Required traces: `time`, `VDD`, `VSS`, `OUT_P`.

The required trace names are: `time`, `VDD`, `VSS`, `VINP`, `VINN`, `OUT_P`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
