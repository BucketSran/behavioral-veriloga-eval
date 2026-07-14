# Smooth Comparator Tanh Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `smooth_comparator_tanh.va`:
  - Module `smooth_comparator_tanh` (entry)
    - position 0: `sigin` (input, electrical)
    - position 1: `sigref` (input, electrical)
    - position 2: `sigout` (output, electrical)

## Public Parameter Contract

- `smooth_comparator_tanh.high` defaults to `1`; valid range: finite; overrides high.
- `smooth_comparator_tanh.low` defaults to `-1`; valid range: finite; overrides low.
- `smooth_comparator_tanh.offset` defaults to `0`; valid range: finite; overrides offset.
- `smooth_comparator_tanh.comp_slope` defaults to `1000`; valid range: finite; overrides comp_slope.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_TANH_TRANSFER`: restore: Drive `sigout` as `0.5 * (high - low) * tanh(comp_slope * (V(sigin, sigref) - offset)) + 0.5 * (high + low)`. Required traces: `time`, `sigin`, `sigref`, `sigout`.
- `P_INPUT_POLARITY`: restore: A larger `V(sigin, sigref)` must move the output toward `high`, not toward `low`. Required traces: `time`, `sigin`, `sigref`, `sigout`.
- `P_SMOOTH_TRANSITION`: restore: The output must transition smoothly between `low` and `high` according to the tanh slope, not as a hard switch. Required traces: `time`, `sigin`, `sigref`, `sigout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `smooth_comparator_tanh.va`.
Every supplied `.va` file is editable; do not add or omit files.
