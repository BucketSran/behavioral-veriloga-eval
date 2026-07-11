# DWA DEM Encoder Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `DWA DEM Encoder` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `dwa_ptr_gen.va`:
  - Module `dwa_ptr_gen` (entry)
    - position 0: `clk_i` (input, electrical)
    - position 1: `rst_ni` (input, electrical)
    - position 2: `code_msb_i[3:0]` (input, electrical)
    - position 3: `cell_en_o[15:0]` (output, electrical)
    - position 4: `ptr_o[15:0]` (output, electrical)
- Artifact `v2b_4b.va`:
  - Module `v2b_4b` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `vin` (input, electrical)
    - position 2: `out_3` (output, electrical)
    - position 3: `out_2` (output, electrical)
    - position 4: `out_1` (output, electrical)
    - position 5: `out_0` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `v2b_4b` as `XV2B` with ordered public binding: clk=clk, vin=vin, out_3=code_bus[3], out_2=code_bus[2], out_1=code_bus[1], out_0=code_bus[0].
- Instantiate `dwa_ptr_gen` as `XDWA` with ordered public binding: clk_i=clk, rst_ni=rst_n, code_msb_i[3:0]=code_bus[3:0], cell_en_o[15:0]=cell_en[15:0], ptr_o[15:0]=ptr[15:0].

## Public Parameter Contract

- `dwa_ptr_gen.vdd` defaults to `0.9` V; valid range: vdd > 0; sets logic-high output level.
- `dwa_ptr_gen.vth` defaults to `0.45` V; valid range: 0 < vth < vdd; sets input logic threshold.
- `dwa_ptr_gen.ptr_init` defaults to `0` index; valid range: 0 <= ptr_init <= 15; sets reset pointer position in the circular element array.
- `v2b_4b.vdd` defaults to `0.9` V; valid range: vdd > 0; sets output high level and twice the clock threshold.
- `v2b_4b.tedge` defaults to `1e-10` s; valid range: tedge > 0; sets output-bit transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_V2B_ROUND_AND_CLAMP`: exercise and make observable: On each rising helper clock crossing, vin rounds to the nearest integer and clamps to a four-bit code from 0 through 15. Required traces: `time`, `clk_i`, `vin_node`, `code_3`, `code_2`, `code_1`, `code_0`.
- `P_ACTIVE_LOW_RESET_POINTER`: exercise and make observable: A sampled active-low reset initializes ptr to the one-hot ptr_init position. Required traces: `time`, `clk_i`, `rst_ni`, `ptr_15`, `ptr_14`, `ptr_13`, `ptr_12`, `ptr_11`, `ptr_10`, `ptr_9`, `ptr_8`, `ptr_7`, `ptr_6`, `ptr_5`, `ptr_4`, `ptr_3`, `ptr_2`, `ptr_1`, `ptr_0`.
- `P_ROTATING_POINTER_UPDATE`: exercise and make observable: Each post-reset rising edge advances the circular pointer by the sampled unsigned code modulo 16. Required traces: `time`, `clk_i`, `rst_ni`, `code_3`, `code_2`, `code_1`, `code_0`, `ptr_15`, `ptr_14`, `ptr_13`, `ptr_12`, `ptr_11`, `ptr_10`, `ptr_9`, `ptr_8`, `ptr_7`, `ptr_6`, `ptr_5`, `ptr_4`, `ptr_3`, `ptr_2`, `ptr_1`, `ptr_0`.
- `P_POINTER_ONE_HOT`: exercise and make observable: Ptr remains exactly one-hot at the updated circular pointer position. Required traces: `time`, `ptr_15`, `ptr_14`, `ptr_13`, `ptr_12`, `ptr_11`, `ptr_10`, `ptr_9`, `ptr_8`, `ptr_7`, `ptr_6`, `ptr_5`, `ptr_4`, `ptr_3`, `ptr_2`, `ptr_1`, `ptr_0`.
- `P_DWA_SELECTED_MASK`: exercise and make observable: Cell_en implements the public rotating span and LSB boundary-cell rule for the sampled code, including the code-zero boundary-cell case. Required traces: `time`, `code_3`, `code_2`, `code_1`, `code_0`, `cell_en_15`, `cell_en_14`, `cell_en_13`, `cell_en_12`, `cell_en_11`, `cell_en_10`, `cell_en_9`, `cell_en_8`, `cell_en_7`, `cell_en_6`, `cell_en_5`, `cell_en_4`, `cell_en_3`, `cell_en_2`, `cell_en_1`, `cell_en_0`, `ptr_15`, `ptr_14`, `ptr_13`, `ptr_12`, `ptr_11`, `ptr_10`, `ptr_9`, `ptr_8`, `ptr_7`, `ptr_6`, `ptr_5`, `ptr_4`, `ptr_3`, `ptr_2`, `ptr_1`, `ptr_0`.
- `P_SYSTEM_CODE_BINDING`: exercise and make observable: The four helper outputs feed the DWA code bus in MSB-to-LSB order without bit reversal. Required traces: `time`, `vin_node`, `code_3`, `code_2`, `code_1`, `code_0`, `cell_en_15`, `cell_en_14`, `cell_en_13`, `cell_en_12`, `cell_en_11`, `cell_en_10`, `cell_en_9`, `cell_en_8`, `cell_en_7`, `cell_en_6`, `cell_en_5`, `cell_en_4`, `cell_en_3`, `cell_en_2`, `cell_en_1`, `cell_en_0`, `ptr_15`, `ptr_14`, `ptr_13`, `ptr_12`, `ptr_11`, `ptr_10`, `ptr_9`, `ptr_8`, `ptr_7`, `ptr_6`, `ptr_5`, `ptr_4`, `ptr_3`, `ptr_2`, `ptr_1`, `ptr_0`.

The required trace names are: `time`, `clk_i`, `rst_ni`, `vin_node`, `code_3`, `code_2`, `code_1`, `code_0`, `cell_en_15`, `cell_en_14`, `cell_en_13`, `cell_en_12`, `cell_en_11`, `cell_en_10`, `cell_en_9`, `cell_en_8`, `cell_en_7`, `cell_en_6`, `cell_en_5`, `cell_en_4`, `cell_en_3`, `cell_en_2`, `cell_en_1`, `cell_en_0`, `ptr_15`, `ptr_14`, `ptr_13`, `ptr_12`, `ptr_11`, `ptr_10`, `ptr_9`, `ptr_8`, `ptr_7`, `ptr_6`, `ptr_5`, `ptr_4`, `ptr_3`, `ptr_2`, `ptr_1`, `ptr_0`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
