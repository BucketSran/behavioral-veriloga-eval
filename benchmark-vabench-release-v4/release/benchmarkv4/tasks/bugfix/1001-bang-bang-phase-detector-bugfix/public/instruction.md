# Bang-Bang Phase Detector Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `bbpd_ref.va`:
  - Module `bbpd_ref` (entry)
    - position 0: `data` (input, electrical)
    - position 1: `clk` (input, electrical)
    - position 2: `retimed_data` (input, electrical)
    - position 3: `up` (output, electrical)
    - position 4: `down` (output, electrical)

## Public Parameter Contract

- `bbpd_ref.vdd` defaults to `0.9` V; valid range: vdd > 0; sets the voltage-coded output high level.
- `bbpd_ref.vth` defaults to `0.45` V; valid range: 0 < vth < vdd; sets the data, clock, and retimed-data decision threshold.
- `bbpd_ref.trf` defaults to `1e-11` s; valid range: trf > 0; sets output rise and fall smoothing.
- `bbpd_ref.td` defaults to `0.0` s; valid range: td >= 0; sets output transition delay.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_DIRECTION`: restore: Each data transition selects UP for clock-high/retimed-low, DOWN for clock-low/retimed-high, and neither otherwise. Required traces: `time`, `data`, `clk`, `retimed_data`, `up`, `down`.
- `P_MUTUAL_EXCLUSION`: restore: UP and DOWN are never asserted simultaneously. Required traces: `time`, `up`, `down`.
- `P_PULSE_CLEAR`: restore: An asserted correction output returns low after the next clock transition. Required traces: `time`, `clk`, `up`, `down`.
- `P_RAIL_LEVELS`: restore: Asserted outputs approach vdd and inactive outputs approach 0 V with finite smoothing. Required traces: `time`, `up`, `down`.

## Modeling Constraints

- Use deterministic voltage-domain behavior.
- Keep event-triggered state updates separate from unconditional output contributions.
- Do not add undeclared artifacts, ports, debug outputs, or validation state.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `bbpd_ref.va`.
Every supplied `.va` file is editable; do not add or omit files.
