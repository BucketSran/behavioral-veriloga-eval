Write a Verilog-A module named `dwa_ptr_gen_no_overlap` and a minimal EVAS-compatible Spectre testbench.

# Task: dwa_ptr_gen_no_overlap_smoke

## Objective

Create a pure voltage-domain DWA (Data Weighted Averaging) pointer generator. The model must rotate a 16-cell selection window and ensure consecutive activation windows do not overlap.

## DUT Contract

- Module name: `dwa_ptr_gen_no_overlap`
- Ports, all `electrical`, exactly as named:
  - Inputs: `clk_i`, `rst_ni`, `code_msb_i[3:0]`
  - Outputs: `cell_en_o[15:0]`, `ptr_o[15:0]`
- Parameters:
  - `vdd`
  - `vth`
  - `ptr_init`
- Reset:
  - `rst_ni` is active-low.
  - During reset, outputs should be LOW except for any explicitly defined pointer initialization.
- Clocking:
  - Sample the 4-bit input code on the rising edge of `clk_i`.
  - Use Verilog-A `@(cross(V(clk_i) - vth, +1))`.

## Required Behavior

- Maintain a rotating pointer across 16 cells.
- Produce `cell_en_o[*]` outputs that activate cells according to the sampled code.
- Consecutive non-reset cycles must not reuse the same enabled cell set.
- `ptr_o[*]` must represent the active pointer location as a one-hot or otherwise checker-readable pointer bit vector.
- Output HIGH is `vdd`; output LOW is `0`.

## Testbench Contract

Create `tb_dwa_ptr_gen_no_overlap.scs` that:

- Includes `dwa_ptr_gen_no_overlap.va` via `ahdl_include`.
- Provides a 0.9 V supply behavior through parameters/sources as needed.
- Generates a 100 MHz clock, period 10 ns.
- Holds `rst_ni` low initially, then deasserts reset after about 5 ns.
- Sweeps 4-bit code values to exercise multiple pointer updates.
- Runs transient for about 175 ns.

## Observable CSV Contract

The waveform CSV must expose these exact scalar signal names:

- `clk_i`, `rst_ni`
- `cell_en_0`, `cell_en_1`, `cell_en_2`, `cell_en_3`, `cell_en_4`, `cell_en_5`, `cell_en_6`, `cell_en_7`
- `cell_en_8`, `cell_en_9`, `cell_en_10`, `cell_en_11`, `cell_en_12`, `cell_en_13`, `cell_en_14`, `cell_en_15`
- `ptr_0`, `ptr_1`, `ptr_2`, `ptr_3`, `ptr_4`, `ptr_5`, `ptr_6`, `ptr_7`
- `ptr_8`, `ptr_9`, `ptr_10`, `ptr_11`, `ptr_12`, `ptr_13`, `ptr_14`, `ptr_15`

If the DUT uses vector ports internally, the testbench must still save or expose every bit under the scalar names above. Do not rely only on CSV headers such as `cell_en_o[0]` or `ptr_o[0]`.

## Deliverables

Return exactly two files:

1. `dwa_ptr_gen_no_overlap.va`
2. `tb_dwa_ptr_gen_no_overlap.scs`


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=175n maxstep=0.1n
```

Required public waveform columns in `tran.csv`:

- `time`, `clk_i`, `rst_ni`, `ptr_0`, `ptr_1`, `ptr_2`, `ptr_3`, `ptr_4`
- `ptr_5`, `ptr_6`, `ptr_7`, `ptr_8`, `ptr_9`, `ptr_10`, `ptr_11`, `ptr_12`
- `ptr_13`, `ptr_14`, `ptr_15`, `cell_en_0`, `cell_en_1`, `cell_en_2`, `cell_en_3`, `cell_en_4`
- `cell_en_5`, `cell_en_6`, `cell_en_7`, `cell_en_8`, `cell_en_9`, `cell_en_10`, `cell_en_11`, `cell_en_12`
- `cell_en_13`, `cell_en_14`, `cell_en_15`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Reset-like input(s) `reset`, `rst_ni` must be asserted only for startup/explicit reset checks, then deasserted early enough and kept deasserted through the post-reset checking window.
- For active-low resets such as `rstb`, `rst_n`, or `rst_ni`, avoid a finite-width pulse that returns the reset node low after release; use a waveform that remains high during checking.
- Clock-like input(s) `clock`, `CLK` must provide enough valid edges after reset/enable for the checker to sample settled outputs.
- Sequential outputs are sampled shortly after clock edges, so drive outputs with stable held state variables and `transition()` targets rather than glitchy combinational expressions.
- Public stimulus nodes used by the reference harness include: `clk_i`, `rst_ni`, `vin_node`.
