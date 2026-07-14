# Quadrature LO Generator from Divided Clock Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `quadrature_lo_generator_divided_clock.va`:
  - Module `quadrature_lo_generator_divided_clock` (entry)
    - position 0: `clk_in` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `enable` (input, electrical)
    - position 3: `lo_i` (output, electrical)
    - position 4: `lo_q` (output, electrical)
    - position 5: `div_metric` (output, electrical)
    - position 6: `quad_ok` (output, electrical)

## Public Parameter Contract

- `quadrature_lo_generator_divided_clock.vdd` defaults to `0.9` V; valid range: vdd > vss; sets the logic-high output level.
- `quadrature_lo_generator_divided_clock.vss` defaults to `0.0` V; valid range: vss < vdd; sets the logic-low output level.
- `quadrature_lo_generator_divided_clock.vth` defaults to `0.45` V; valid range: vss < vth < vdd; sets the digital-voltage crossing threshold.
- `quadrature_lo_generator_divided_clock.tr` defaults to `2e-10` s; valid range: tr > 0; sets transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_DISABLE_CLEAR`: restore: Reset or disable clears both LO outputs, state metric, and quad_ok. Required traces: `time`, `clk_in`, `rst`, `enable`, `lo_i`, `lo_q`, `div_metric`, `quad_ok`.
- `P_QUADRATURE_SEQUENCE`: restore: Enabled rising input edges drive the repeating 10, 11, 01, 00 sequence. Required traces: `time`, `clk_in`, `rst`, `enable`, `lo_i`, `lo_q`, `div_metric`, `quad_ok`.
- `P_DIVIDE_BY_FOUR`: restore: Each LO has one cycle per four input rising edges with equal frequency and deterministic quadrature order. Required traces: `time`, `clk_in`, `rst`, `enable`, `lo_i`, `lo_q`, `div_metric`, `quad_ok`.
- `P_STATE_METRIC`: restore: div_metric reports the currently driven sequence index as k/3 of the output span. Required traces: `time`, `clk_in`, `rst`, `enable`, `lo_i`, `lo_q`, `div_metric`, `quad_ok`.
- `P_QUAD_OK_DELAY`: restore: quad_ok asserts only after two complete four-state output cycles. Required traces: `time`, `clk_in`, `rst`, `enable`, `lo_i`, `lo_q`, `div_metric`, `quad_ok`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not use current contributions, transistor-level devices, validation logic, or simulator side channels.
- Do not hard-code evaluator stimulus timing, stop times, sample windows, or checker tolerances.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `quadrature_lo_generator_divided_clock.va`.
Every supplied `.va` file is editable; do not add or omit files.
