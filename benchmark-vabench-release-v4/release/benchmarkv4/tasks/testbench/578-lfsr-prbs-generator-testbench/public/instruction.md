# LFSR PRBS Generator Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `LFSR PRBS Generator` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `prbs7_ref` as `XDUT` with ordered public binding: clk=clk, rst_n=rst_n, en=en, serial_out=serial_out, state_0=state_0, state_1=state_1, state_2=state_2, state_3=state_3, state_4=state_4, state_5=state_5, state_6=state_6.

## Public Parameter Contract

- `prbs7_ref.vdd` defaults to `0.9` V; valid range: vdd > 0; sets serial_out and state-bit high levels.
- `prbs7_ref.vth` defaults to `0.45` V; valid range: 0 < vth < vdd; sets the clock, reset, and enable decision threshold.
- `prbs7_ref.trf` defaults to `1e-11` s; valid range: trf > 0; sets rise and fall smoothing for every output.
- `prbs7_ref.td` defaults to `0.0` s; valid range: td >= 0; sets transition delay for every output.
- `prbs7_ref.seed` defaults to `127`; valid range: integer 0 through 127 inclusive; values outside this range are invalid public overrides; sets the seven-bit reset state; seed 0 is remapped to 7'b0000001 to avoid the LFSR lock-up state.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_SEED`: exercise and make observable: When rst_n is below vth, the exposed seven-bit state is loaded from seed[6:0]; legal seed overrides are integers 0 through 127 inclusive, and seed 0 is remapped to 7'b0000001 to avoid the LFSR lock-up state. Required traces: `time`, `rst_n`, `state_0`, `state_1`, `state_2`, `state_3`, `state_4`, `state_5`, `state_6`.
- `P_ENABLE_GATING`: exercise and make observable: On rising clk crossings, the state advances only when rst_n and en are both above vth; otherwise it holds or resets as applicable. Required traces: `time`, `clk`, `rst_n`, `en`, `state_0`, `state_1`, `state_2`, `state_3`, `state_4`, `state_5`, `state_6`.
- `P_FEEDBACK_POLYNOMIAL`: exercise and make observable: Each enabled update sets next state_0 to previous state_6 XOR previous state_5, implementing x^7 + x^6 + 1. Required traces: `time`, `clk`, `en`, `state_0`, `state_5`, `state_6`.
- `P_SHIFT_SEQUENCE`: exercise and make observable: Each enabled update sets next state_i to previous state_(i-1) for i from 1 through 6. Required traces: `time`, `clk`, `en`, `state_0`, `state_1`, `state_2`, `state_3`, `state_4`, `state_5`, `state_6`.
- `P_SERIAL_OUTPUT`: exercise and make observable: serial_out always represents the current state_6 bit. Required traces: `time`, `serial_out`, `state_6`.
- `P_OUTPUT_LEVELS`: exercise and make observable: serial_out and every state output use 0 V and vdd levels with delay td and transition smoothing trf. Required traces: `time`, `serial_out`, `state_0`, `state_1`, `state_2`, `state_3`, `state_4`, `state_5`, `state_6`.

The required trace names are: `time`, `clk`, `rst_n`, `en`, `serial_out`, `state_0`, `state_1`, `state_2`, `state_3`, `state_4`, `state_5`, `state_6`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
