# DAC Mismatch Unit Weighting Model Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `dac_mismatch_unit_weighting_model.va`:
  - Module `dac_mismatch_unit_weighting_model` (entry)
    - position 0: `b0` (input, electrical)
    - position 1: `b1` (input, electrical)
    - position 2: `b2` (input, electrical)
    - position 3: `b3` (input, electrical)
    - position 4: `out` (output, electrical)

## Public Parameter Contract

- `dac_mismatch_unit_weighting_model.vhi` defaults to `0.9` V; valid range: vhi > vlo; sets the all-active output endpoint.
- `dac_mismatch_unit_weighting_model.vlo` defaults to `0.0` V; valid range: vlo < vhi; sets the all-zero output endpoint.
- `dac_mismatch_unit_weighting_model.tr` defaults to `1e-10` s; valid range: tr > 0; sets output transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ZERO_AND_FULL_SCALE`: restore: All-zero input maps to vlo and all-active input maps to vhi after transition settling. Required traces: `time`, `b0`, `b1`, `b2`, `b3`, `out`.
- `P_NONIDEAL_WEIGHT_SUM`: restore: Inputs b0 through b3 contribute fixed positive weights 1.00, 2.02, 3.96, and 8.08 normalized by their all-active sum. Required traces: `time`, `b0`, `b1`, `b2`, `b3`, `out`.
- `P_LOGIC_THRESHOLD`: restore: Each bit is independently interpreted using the public fixed 0.45 V decision threshold. Required traces: `time`, `b0`, `b1`, `b2`, `b3`, `out`.
- `P_BOUNDED_OUTPUT`: restore: For every input pattern, the settled output remains within the vlo-to-vhi interval. Required traces: `time`, `b0`, `b1`, `b2`, `b3`, `out`.
- `P_MISMATCH_OBSERVABILITY`: restore: Single-bit output increments preserve the stated nonideal weighting rather than ideal powers-of-two weighting. Required traces: `time`, `b0`, `b1`, `b2`, `b3`, `out`.

## Modeling Constraints

- Use the public fixed nonideal weights and deterministic voltage-domain reconstruction.
- Use smoothed voltage contributions only.
- Do not use current contributions, ddt(), idt(), validation hooks, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `dac_mismatch_unit_weighting_model.va`.
Every supplied `.va` file is editable; do not add or omit files.
