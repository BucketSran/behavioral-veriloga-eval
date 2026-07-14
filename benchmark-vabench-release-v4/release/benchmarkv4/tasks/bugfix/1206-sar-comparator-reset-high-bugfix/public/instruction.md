# SAR Comparator Reset High Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `sar_comparator_reset_high.va`:
  - Module `sar_comparator_reset_high` (entry)
    - position 0: `cmpck` (input, electrical)
    - position 1: `vinn` (input, electrical)
    - position 2: `vinp` (input, electrical)
    - position 3: `dcmpn` (output, electrical)
    - position 4: `dcmpp` (output, electrical)

## Public Parameter Contract

- `sar_comparator_reset_high.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `sar_comparator_reset_high.td_cmp` defaults to `20p`; valid range: finite; overrides td_cmp.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_INITIALIZE_BOTH_DECISION_OUTPUTS_HIGH_WHENEVER`: restore: Initialize both decision outputs high. Whenever `cmpck` falls through `vdd/2`, reset both outputs high. Whenever `cmpck` rises through `vdd/2`, latch a differential decision: `dcmpp` high for `vinp > vinn`, `dcmpn` high for `vinp < vinn`, and both outputs low for equal inputs. Hold the latched or reset state until the next clock event. Required traces: `time`, `cmpck`, `dcmpn`, `dcmpp`, `vinn`, `vinp`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `sar_comparator_reset_high.va`.
Every supplied `.va` file is editable; do not add or omit files.
