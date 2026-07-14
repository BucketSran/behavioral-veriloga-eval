# Hysteresis Comparator Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `cmp_hysteresis.va`:
  - Module `cmp_hysteresis` (entry)
    - position 0: `VINN` (input, electrical)
    - position 1: `VINP` (input, electrical)
    - position 2: `OUTN` (output, electrical)
    - position 3: `OUTP` (output, electrical)
    - position 4: `VSS` (input, electrical)
    - position 5: `VDD` (input, electrical)

## Public Parameter Contract

- `cmp_hysteresis.vhys` defaults to `0.01` V; valid range: vhys >= 0; sets total differential hysteresis width centered at zero.
- `cmp_hysteresis.tedge` defaults to `5e-11` s; valid range: tedge > 0; sets complementary output transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_INITIAL_DECISION`: restore: OUTP initializes high only when the initial differential exceeds positive vhys over two; otherwise OUTP initializes low and OUTN high. Required traces: `time`, `vinp`, `vinn`, `out_p`, `out_n`.
- `P_POSITIVE_SWITCH_THRESHOLD`: restore: The low OUTP state switches high only on a rising differential crossing of positive vhys over two. Required traces: `time`, `vinp`, `vinn`, `out_p`, `out_n`.
- `P_NEGATIVE_SWITCH_THRESHOLD`: restore: The high OUTP state switches low only on a falling differential crossing of negative vhys over two. Required traces: `time`, `vinp`, `vinn`, `out_p`, `out_n`.
- `P_HYSTERESIS_HOLD`: restore: The previous decision is retained while the differential remains inside the hysteresis band. Required traces: `time`, `vinp`, `vinn`, `out_p`, `out_n`.
- `P_COMPLEMENTARY_RAIL_OUTPUT`: restore: OUTP and OUTN remain complementary and use the local VDD and VSS rail levels after smoothing. Required traces: `time`, `out_p`, `out_n`, `vdd`, `vss`.

## Modeling Constraints

- Update retained decision state only at initialization and differential threshold crossings.
- Drive complementary smoothed voltage contributions outside event blocks.
- Do not use current contributions, ddt(), idt(), validation hooks, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `cmp_hysteresis.va`.
Every supplied `.va` file is editable; do not add or omit files.
