# SUM5 Signed SAR Weight Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `SUM5 Signed SAR Weight` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `sum5_signed_sar_weight.va`:
  - Module `sum5_signed_sar_weight` (entry)
    - position 0: `d1` (input, electrical)
    - position 1: `d2` (input, electrical)
    - position 2: `d3` (input, electrical)
    - position 3: `d4` (input, electrical)
    - position 4: `d5` (input, electrical)
    - position 5: `out` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `sum5_signed_sar_weight` as `XDUT` with ordered public binding: d1=d1, d2=d2, d3=d3, d4=d4, d5=d5, out=out.

## Public Parameter Contract

- `sum5_signed_sar_weight.vth` defaults to `0.55`; valid range: finite; overrides vth.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_TREAT_EACH_DECISION_INPUT_AS_1`: exercise and make observable: Treat each decision input as `+1` when its voltage is above `vth` and `-1` otherwise. Combine the signed decisions with SAR weights `d5 = 1/2`, `d4 = 1/4`, `d3 = 1/8`, `d2 = 1/16`, and `d1 = 1/32`. Drive `out` to the scaled signed reconstruction: Required traces: `time`, `d1`, `d2`, `d3`, `d4`, `d5`, `out`.
- `P_TEXT_OUT_1_1_2_SIGNED`: exercise and make observable: ```text out = 1.1 * (2 * signed_weighted_sum - 1) ``` Required traces: `time`, `d1`, `d2`, `d3`, `d4`, `d5`, `out`.
- `P_THE_BEHAVIOR_IS_CONTINUOUS_WITH_RESPECT`: exercise and make observable: The behavior is continuous with respect to the voltage-coded decision inputs after thresholding. Required traces: `time`, `d1`, `d2`, `d3`, `d4`, `d5`, `out`.

The required trace names are: `time`, `d1`, `d2`, `d3`, `d4`, `d5`, `out`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
