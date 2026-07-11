# Clock Divider Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Clock Divider` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `clk_divider_ref` as `XDUT` with ordered public binding: clk_in=clk_in, rst_n=rst_n, div_code_0=div_code_0, div_code_1=div_code_1, div_code_2=div_code_2, div_code_3=div_code_3, div_code_4=div_code_4, div_code_5=div_code_5, div_code_6=div_code_6, div_code_7=div_code_7, clk_out=clk_out, lock=lock.

## Public Parameter Contract

- `clk_divider_ref.vdd` defaults to `0.9` V; valid range: vdd > 0; sets output high levels.
- `clk_divider_ref.vth` defaults to `0.45` V; valid range: 0 < vth < vdd; sets clock, reset, and code thresholds.
- `clk_divider_ref.trf` defaults to `1e-11` s; valid range: trf > 0; sets output rise and fall smoothing.
- `clk_divider_ref.td` defaults to `0.0` s; valid range: td >= 0; sets output transition delay.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET`: exercise and make observable: Active-low reset clears divider phase and drives clk_out and lock low. Required traces: `time`, `clk_in`, `rst_n`, `clk_out`, `lock`.
- `P_RATIO_DECODE`: exercise and make observable: The LSB-first 8-bit code selects the divide ratio, with code zero mapped to ratio one. Required traces: `time`, `clk_in`, `div_code_0`, `div_code_1`, `div_code_2`, `div_code_3`, `div_code_4`, `div_code_5`, `div_code_6`, `div_code_7`, `clk_out`.
- `P_DIVIDED_PERIOD`: exercise and make observable: For ratios above one, successive clk_out rising edges span the decoded number of clk_in rising edges. Required traces: `time`, `clk_in`, `clk_out`.
- `P_ODD_RATIO_DUTY`: exercise and make observable: Odd ratios retain both phases with floor/ceil segment lengths differing by at most one input cycle. Required traces: `time`, `clk_in`, `clk_out`.
- `P_LOCK_REACQUIRE`: exercise and make observable: lock asserts after one complete output period and clears/reacquires when the ratio changes. Required traces: `time`, `clk_in`, `rst_n`, `div_code_0`, `div_code_1`, `div_code_2`, `div_code_3`, `div_code_4`, `div_code_5`, `div_code_6`, `div_code_7`, `clk_out`, `lock`.

The required trace names are: `time`, `clk_in`, `rst_n`, `div_code_0`, `div_code_1`, `div_code_2`, `div_code_3`, `div_code_4`, `div_code_5`, `div_code_6`, `div_code_7`, `clk_out`, `lock`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
