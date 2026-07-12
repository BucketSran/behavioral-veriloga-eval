# PFD Tdomain Reset Window Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `pfd_tdomain_reset_window.va`:
  - Module `pfd_tdomain_reset_window` (entry)
    - position 0: `in1` (input, electrical)
    - position 1: `in2` (input, electrical)
    - position 2: `up` (output, electrical)
    - position 3: `dn` (output, electrical)
    - position 4: `vdd` (input, electrical)
    - position 5: `gnd` (input, electrical)

## Public Parameter Contract

- `pfd_tdomain_reset_window.ttol` defaults to `5f`; valid range: finite; overrides ttol.
- `pfd_tdomain_reset_window.td` defaults to `0`; valid range: finite; overrides td.
- `pfd_tdomain_reset_window.tt` defaults to `10p`; valid range: finite; overrides tt.
- `pfd_tdomain_reset_window.ton` defaults to `120p`; valid range: finite; overrides ton.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_LEADING_EDGE_DIRECTION`: restore: A leading `in1` edge asserts `up`, and a leading `in2` edge asserts `dn`. Required traces: `time`, `dn`, `in1`, `in2`, `up`, `vdd`, `gnd`.
- `P_RESET_OVERLAP_WINDOW`: restore: After both inputs arrive, both outputs remain asserted for the `ton` reset-overlap window. Required traces: `time`, `dn`, `in1`, `in2`, `up`, `vdd`, `gnd`.
- `P_CLEAR_AFTER_RESET_WINDOW`: restore: After the reset-overlap window, both `up` and `dn` clear before the next phase event. Required traces: `time`, `dn`, `in1`, `in2`, `up`, `vdd`, `gnd`.
- `P_PFD_OUTPUT_LEVELS`: restore: `up` and `dn` use rail-referenced voltage-coded low/high levels. Required traces: `time`, `dn`, `in1`, `in2`, `up`, `vdd`, `gnd`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `pfd_tdomain_reset_window.va`.
Every supplied `.va` file is editable; do not add or omit files.
