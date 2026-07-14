# Start Gated Offset Search Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `start_gated_offset_search.va`:
  - Module `start_gated_offset_search` (entry)
    - position 0: `CLK` (input, electrical)
    - position 1: `VOUT` (input, electrical)
    - position 2: `START` (input, electrical)
    - position 3: `VINP` (output, electrical)
    - position 4: `VINN` (output, electrical)

## Public Parameter Contract

- `start_gated_offset_search.vdd` defaults to `0.9` V; valid range: vdd > 0; sets twice the CLK and VOUT decision threshold.
- `start_gated_offset_search.vcm` defaults to `0.7` V; valid range: finite real; sets the common mode of VINP and VINN.
- `start_gated_offset_search.vstart_th` defaults to `0.45` V; valid range: finite real; sets the START enable and reinitialization threshold.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_DISABLED_COMMON_MODE`: restore: While START is below vstart_th, VINP and VINN both equal vcm and the internal search state is reset. Required traces: `time`, `start`, `vinp`, `vinn`.
- `P_START_REINITIALIZATION`: restore: Each rising START crossing through vstart_th reinitializes differential value to zero, step to 20 mV, and remembered direction high. Required traces: `time`, `start`, `vinp`, `vinn`.
- `P_FALLING_CLOCK_UPDATES`: restore: While START is high, search updates occur only on falling CLK crossings through vdd/2. Required traces: `time`, `clk`, `start`, `vout`, `vinp`, `vinn`.
- `P_DECISION_DIRECTED_STEP`: restore: At each enabled update, VOUT above vdd/2 moves the differential value positive and VOUT at or below vdd/2 moves it negative. Required traces: `time`, `clk`, `vout`, `vinp`, `vinn`.
- `P_REVERSAL_STEP_HALVING`: restore: When the newly sampled decision direction differs from the remembered direction, the current step is halved before applying the move. Required traces: `time`, `clk`, `vout`, `vinp`, `vinn`.
- `P_COMMON_MODE_AND_DIFFERENTIAL`: restore: During search, the average of VINP and VINN remains vcm and their difference equals the accumulated differential search value. Required traces: `time`, `start`, `vinp`, `vinn`.

## Modeling Constraints

- Gate and reinitialize the search from START and update it only on falling CLK events.
- Maintain symmetric voltage-domain outputs around the public vcm parameter.
- Do not use current contributions, ddt(), idt(), validation hooks, hard-coded waveform sample points, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `start_gated_offset_search.va`.
Every supplied `.va` file is editable; do not add or omit files.
