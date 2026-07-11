# DWA DEM Encoder

## Task Contract

Implement two Verilog-A DUT artifacts for a voltage-domain data-weighted-averaging dynamic-element-matching encoder and its companion voltage-to-binary helper.
- Target artifacts: `dwa_ptr_gen.va`, `v2b_4b.va`

## Public Verilog-A Interface

`dwa_ptr_gen.va` must declare module `dwa_ptr_gen` with positional ports `clk_i`, `rst_ni`, `code_msb_i`, `cell_en_o`, `ptr_o`.

- `clk_i`: input electrical clock.
- `rst_ni`: input electrical active-low reset.
- `code_msb_i[3:0]`: input electrical 4-bit code bus.
- `cell_en_o[15:0]`: output electrical selected unit-element window.
- `ptr_o[15:0]`: output electrical one-hot rotating pointer.

`v2b_4b.va` must declare module `v2b_4b` with positional ports `clk`, `vin`, `out_3`, `out_2`, `out_1`, `out_0`.

## Public Parameter Contract

For `dwa_ptr_gen`, provide these overrideable public parameters:

- `vdd = 0.9 V`: logic high output level for `cell_en_o` and `ptr_o`.
- `vth = 0.45 V`: logic threshold for `clk_i`, `rst_ni`, and `code_msb_i`.
- `ptr_init = 0`: reset pointer index in the 16-element circular array.

For `v2b_4b`, provide these overrideable public parameters:

- `vdd = 0.9 V`: logic high output level and clock threshold reference.
- `tedge = 100 ps`: transition smoothing time for the output bits.

## Required Behavior

For `dwa_ptr_gen`:

- Treat `clk_i`, `rst_ni`, and each `code_msb_i` bit as voltage-coded logic using threshold `vth`.
- Reset initializes the one-hot pointer to `ptr_init`.
- Decode `code_msb_i[3:0]` as an unsigned integer from 0 to 15.
- On each post-reset rising clock edge, sample the code and update `ptr_next = (ptr_prev + code) % 16`.
- Drive `ptr_o` as a one-hot output at `ptr_next`.
- Drive `cell_en_o` as the DWA selected-cell mask for that sampled code: assert the rotating MSB span ending at `ptr_next`, plus the LSB boundary cell at `lsb_idx = (ptr_next - code + 16) % 16`.
- Equivalently, for each cell index `j`, assert `cell_en_o[j]` when `((ptr_next - j + 16) % 16) < code` or `j == lsb_idx`; drive all other cells low.
- For code 0, only the LSB boundary cell is high.

For `v2b_4b`:

- Treat `clk` as voltage-coded logic with a threshold of `0.5 * vdd`.
- On each rising `clk` crossing, convert `V(vin)` to the nearest integer code using `floor(V(vin) + 0.5)`.
- Clamp the code to the 0 to 15 range.
- Drive `out_3..out_0` as a 4-bit binary code with `out_3` as the most significant bit.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A. Use voltage contributions only; do not use current contributions, `ddt()`, or `idt()`. Keep vector bit behavior observable through the declared electrical bus ports. Do not add extra ports, files, debug outputs, pass/fail flags, or state observables that are not part of the public interface.

## Output Contract

Return exactly these complete source artifacts:

- `dwa_ptr_gen.va`
- `v2b_4b.va`
