# Debounce Latch Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `debounce_latch.va`:
  - Module `debounce_latch` (entry)
    - position 0: `sig` (input, electrical)
    - position 1: `rst_n` (input, electrical)
    - position 2: `out` (output, electrical)

## Public Parameter Contract

- `debounce_latch.vth` defaults to `0.45` V; valid range: 0 < vth < vdd; sets sig and rst_n decision threshold.
- `debounce_latch.vdd` defaults to `0.9` V; valid range: vdd > 0; sets output high level.
- `debounce_latch.stable` defaults to `1.2e-08` s; valid range: stable >= 0; sets rising-decision qualification duration.
- `debounce_latch.tr` defaults to `5e-10` s; valid range: tr > 0; sets output transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ACTIVE_LOW_RESET`: restore: out is low and pending qualification is cancelled whenever rst_n is below vth. Required traces: `time`, `rst_n`, `out`.
- `P_RISE_QUALIFICATION`: restore: A sig rising edge sets out high only after sig and rst_n remain high for stable seconds. Required traces: `time`, `sig`, `rst_n`, `out`.
- `P_FALL_CLEAR`: restore: A sig falling edge clears out and cancels pending qualification. Required traces: `time`, `sig`, `out`.
- `P_EVENT_HOLD`: restore: out holds between reset, sig-edge, and qualification-timer events. Required traces: `time`, `sig`, `rst_n`, `out`.

## Modeling Constraints

- Use voltage contributions only.
- Keep event state updates separate from unconditional finite-smoothing output contribution.
- Do not use current contributions, ddt(), idt(), validation logic, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `debounce_latch.va`.
Every supplied `.va` file is editable; do not add or omit files.
