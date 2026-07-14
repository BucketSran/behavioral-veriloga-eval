# SUM5 Signed SAR Weight Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `sum5_signed_sar_weight.va`:
  - Module `sum5_signed_sar_weight` (entry)
    - position 0: `d1` (input, electrical)
    - position 1: `d2` (input, electrical)
    - position 2: `d3` (input, electrical)
    - position 3: `d4` (input, electrical)
    - position 4: `d5` (input, electrical)
    - position 5: `out` (output, electrical)

## Public Parameter Contract

- `sum5_signed_sar_weight.vth` defaults to `0.55`; valid range: finite; overrides vth.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_TREAT_EACH_DECISION_INPUT_AS_1`: restore: Treat each decision input as `+1` when its voltage is above `vth` and `-1` otherwise. Combine the signed decisions with SAR weights `d5 = 1/2`, `d4 = 1/4`, `d3 = 1/8`, `d2 = 1/16`, and `d1 = 1/32`. Drive `out` to the scaled signed reconstruction: Required traces: `time`, `d1`, `d2`, `d3`, `d4`, `d5`, `out`.
- `P_TEXT_OUT_1_1_2_SIGNED`: restore: ```text out = 1.1 * (2 * signed_weighted_sum - 1) ``` Required traces: `time`, `d1`, `d2`, `d3`, `d4`, `d5`, `out`.
- `P_THE_BEHAVIOR_IS_CONTINUOUS_WITH_RESPECT`: restore: The behavior is continuous with respect to the voltage-coded decision inputs after thresholding. Required traces: `time`, `d1`, `d2`, `d3`, `d4`, `d5`, `out`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `sum5_signed_sar_weight.va`.
Every supplied `.va` file is editable; do not add or omit files.
