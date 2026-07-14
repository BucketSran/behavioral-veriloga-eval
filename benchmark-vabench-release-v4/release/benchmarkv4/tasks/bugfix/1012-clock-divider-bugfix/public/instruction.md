# Clock Divider Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `clk_divider_ref.va`:
  - Module `clk_divider_ref` (entry)
    - position 0: `clk_in` (input, electrical)
    - position 1: `rst_n` (input, electrical)
    - position 2: `div_code_0` (input, electrical)
    - position 3: `div_code_1` (input, electrical)
    - position 4: `div_code_2` (input, electrical)
    - position 5: `div_code_3` (input, electrical)
    - position 6: `div_code_4` (input, electrical)
    - position 7: `div_code_5` (input, electrical)
    - position 8: `div_code_6` (input, electrical)
    - position 9: `div_code_7` (input, electrical)
    - position 10: `clk_out` (output, electrical)
    - position 11: `lock` (output, electrical)

## Public Parameter Contract

- `clk_divider_ref.vdd` defaults to `0.9` V; valid range: vdd > 0; sets output high levels.
- `clk_divider_ref.vth` defaults to `0.45` V; valid range: 0 < vth < vdd; sets clock, reset, and code thresholds.
- `clk_divider_ref.trf` defaults to `1e-11` s; valid range: trf > 0; sets output rise and fall smoothing.
- `clk_divider_ref.td` defaults to `0.0` s; valid range: td >= 0; sets output transition delay.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET`: restore: Active-low reset clears divider phase and drives clk_out and lock low. Required traces: `time`, `clk_in`, `rst_n`, `clk_out`, `lock`.
- `P_RATIO_DECODE`: restore: The LSB-first 8-bit code selects the divide ratio, with code zero mapped to ratio one. Required traces: `time`, `clk_in`, `div_code_0`, `div_code_1`, `div_code_2`, `div_code_3`, `div_code_4`, `div_code_5`, `div_code_6`, `div_code_7`, `clk_out`.
- `P_DIVIDED_PERIOD`: restore: For ratios above one, successive clk_out rising edges span the decoded number of clk_in rising edges. Required traces: `time`, `clk_in`, `clk_out`.
- `P_ODD_RATIO_DUTY`: restore: Odd ratios retain both phases with floor/ceil segment lengths differing by at most one input cycle. Required traces: `time`, `clk_in`, `clk_out`.
- `P_LOCK_REACQUIRE`: restore: lock asserts after one complete output period and clears/reacquires when the ratio changes. Required traces: `time`, `clk_in`, `rst_n`, `div_code_0`, `div_code_1`, `div_code_2`, `div_code_3`, `div_code_4`, `div_code_5`, `div_code_6`, `div_code_7`, `clk_out`, `lock`.

## Modeling Constraints

- Use deterministic voltage-domain behavior.
- Use voltage contributions and finite smoothing only.
- Do not use current contributions, continuous operators, transistor devices, validation hooks, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `clk_divider_ref.va`.
Every supplied `.va` file is editable; do not add or omit files.
