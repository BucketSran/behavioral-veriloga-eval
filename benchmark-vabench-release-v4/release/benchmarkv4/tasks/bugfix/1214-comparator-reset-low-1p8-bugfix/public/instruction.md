# Comparator Reset Low 1p8 Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `comparator_reset_low_1p8.va`:
  - Module `comparator_reset_low_1p8` (entry)
    - position 0: `cmpck` (input, electrical)
    - position 1: `vinn` (input, electrical)
    - position 2: `vinp` (input, electrical)
    - position 3: `dcmpn` (output, electrical)
    - position 4: `dcmpp` (output, electrical)

## Public Parameter Contract

- `comparator_reset_low_1p8.vdd` defaults to `1.8`; valid range: finite; overrides vdd.
- `comparator_reset_low_1p8.td_cmp` defaults to `100p`; valid range: finite; overrides td_cmp.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_INITIALIZE_BOTH_DECISION_OUTPUTS_LOW_WHENEVER`: restore: Initialize both decision outputs low. Whenever `cmpck` falls through `vdd/2`, reset both outputs low. Whenever `cmpck` rises through `vdd/2`, latch a differential decision: drive `dcmpp` high for `vinp > vinn`, drive `dcmpn` high for `vinp < vinn`, and keep both outputs low for an equal-input decision. Hold the latched or reset state until the next clock event. Required traces: `time`, `cmpck`, `dcmpn`, `dcmpp`, `vinn`, `vinp`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `comparator_reset_low_1p8.va`.
Every supplied `.va` file is editable; do not add or omit files.
