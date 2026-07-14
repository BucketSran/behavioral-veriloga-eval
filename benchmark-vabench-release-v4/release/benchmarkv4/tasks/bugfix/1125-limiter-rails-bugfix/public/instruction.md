# Limiter Rails Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `limiter_rails.va`:
  - Module `limiter_rails` (entry)
    - position 0: `vdd` (input, electrical)
    - position 1: `vss` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `vmax` (input, electrical)
    - position 4: `vmin` (input, electrical)
    - position 5: `vout` (output, electrical)

## Public Parameter Contract

- No public parameter is declared.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RAIL_DERIVED_LIMITS`: restore: Derive the upper limit as `V(vdd) - V(vmax)` and the lower limit as `V(vss) + V(vmin)`. Required traces: `time`, `vdd`, `vss`, `vin`, `vmax`, `vmin`, `vout`.
- `P_PASS_WITHIN_LIMITS`: restore: When `V(vin)` lies between the derived limits, drive `vout` to `V(vin)`. Required traces: `time`, `vin`, `vout`.
- `P_LIMIT_ABOVE_UPPER`: restore: When `V(vin)` exceeds the upper limit, drive `vout` to the upper limit. Required traces: `time`, `vdd`, `vin`, `vmax`, `vout`.
- `P_LIMIT_BELOW_LOWER`: restore: When `V(vin)` is below the lower limit, drive `vout` to the lower limit. Required traces: `time`, `vss`, `vin`, `vmin`, `vout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `limiter_rails.va`.
Every supplied `.va` file is editable; do not add or omit files.
