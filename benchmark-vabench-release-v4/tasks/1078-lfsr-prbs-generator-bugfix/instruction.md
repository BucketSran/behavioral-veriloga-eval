# LFSR PRBS Generator Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `prbs7_ref.va`:
  - Module `prbs7_ref` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst_n` (input, electrical)
    - position 2: `en` (input, electrical)
    - position 3: `serial_out` (output, electrical)
    - position 4: `state_0` (output, electrical)
    - position 5: `state_1` (output, electrical)
    - position 6: `state_2` (output, electrical)
    - position 7: `state_3` (output, electrical)
    - position 8: `state_4` (output, electrical)
    - position 9: `state_5` (output, electrical)
    - position 10: `state_6` (output, electrical)

## Public Parameter Contract

- `prbs7_ref.vdd` defaults to `0.9` V; valid range: vdd > 0; sets serial_out and state-bit high levels.
- `prbs7_ref.vth` defaults to `0.45` V; valid range: 0 < vth < vdd; sets the clock, reset, and enable decision threshold.
- `prbs7_ref.trf` defaults to `1e-11` s; valid range: trf > 0; sets rise and fall smoothing for every output.
- `prbs7_ref.td` defaults to `0.0` s; valid range: td >= 0; sets transition delay for every output.
- `prbs7_ref.seed` defaults to `127`; valid range: integer 0 through 127 inclusive; values outside this range are invalid public overrides; sets the seven-bit reset state; seed 0 is remapped to 7'b0000001 to avoid the LFSR lock-up state.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_SEED`: restore: When rst_n is below vth, the exposed seven-bit state is loaded from seed[6:0]; legal seed overrides are integers 0 through 127 inclusive, and seed 0 is remapped to 7'b0000001 to avoid the LFSR lock-up state. Required traces: `time`, `rst_n`, `state_0`, `state_1`, `state_2`, `state_3`, `state_4`, `state_5`, `state_6`.
- `P_ENABLE_GATING`: restore: On rising clk crossings, the state advances only when rst_n and en are both above vth; otherwise it holds or resets as applicable. Required traces: `time`, `clk`, `rst_n`, `en`, `state_0`, `state_1`, `state_2`, `state_3`, `state_4`, `state_5`, `state_6`.
- `P_FEEDBACK_POLYNOMIAL`: restore: Each enabled update sets next state_0 to previous state_6 XOR previous state_5, implementing x^7 + x^6 + 1. Required traces: `time`, `clk`, `en`, `state_0`, `state_5`, `state_6`.
- `P_SHIFT_SEQUENCE`: restore: Each enabled update sets next state_i to previous state_(i-1) for i from 1 through 6. Required traces: `time`, `clk`, `en`, `state_0`, `state_1`, `state_2`, `state_3`, `state_4`, `state_5`, `state_6`.
- `P_SERIAL_OUTPUT`: restore: serial_out always represents the current state_6 bit. Required traces: `time`, `serial_out`, `state_6`.
- `P_OUTPUT_LEVELS`: restore: serial_out and every state output use 0 V and vdd levels with delay td and transition smoothing trf. Required traces: `time`, `serial_out`, `state_0`, `state_1`, `state_2`, `state_3`, `state_4`, `state_5`, `state_6`.

## Modeling Constraints

- Use deterministic rising-edge state updates with active-low reset semantics.
- Preserve the public bit ordering and expose every state bit continuously.
- Do not add undeclared taps, seed ports, files, or validation-only states.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `prbs7_ref.va`.
Every supplied `.va` file is editable; do not add or omit files.
