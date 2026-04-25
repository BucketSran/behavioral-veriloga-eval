Write a Verilog-A module named `dwa_wraparound_ref` and a minimal EVAS-compatible Spectre testbench.

# Task: dwa_wraparound_smoke

## Objective

Create a pure voltage-domain DWA pointer generator that rotates a 16-cell thermometer selection window by the input 4-bit code on every rising clock edge. The smoke test must stress pointer wraparound.

## DUT Contract

- Main module name: `dwa_wraparound_ref`
- If you create a helper code-step module, name it `dwa_code_step_ref`.
- Ports, all `electrical`, exactly as named:
  - Inputs: `clk_i`, `rst_ni`, `code_i[3:0]`
  - Outputs: `cell_en_o[15:0]`, `ptr_o[15:0]`
- Use only voltage-domain Verilog-A constructs.
- Do not use current contributions, `ddt()`, or `idt()`.
- Use `@(cross(V(clk_i) - vth, +1))` for clocked updates.

## Required Behavior

- Start from pointer index 13 after reset.
- The first non-reset update must wrap through cell 15 back to cell 0.
- Later updates must include at least one additional wraparound.
- `ptr_o[*]` must be one-hot after reset and on sampled cycles.
- The active `cell_en_o[*]` count must match the requested input code on each sampled cycle.
- Split selections across the 15-to-0 boundary are allowed and expected when wrapping.

## Testbench Contract

Create a Spectre-compatible testbench that:

- Includes the generated Verilog-A file(s) via `ahdl_include`.
- Generates `clk_i` and active-low `rst_ni`.
- Drives `code_i[3:0]` with values that force wraparound from initial pointer 13.
- Runs long enough to observe at least five post-reset sampled cycles.

## Observable CSV Contract

The waveform CSV must expose these exact scalar signal names:

- `clk_i`, `rst_ni`
- `code_0`, `code_1`, `code_2`, `code_3`
- `cell_en_0`, `cell_en_1`, `cell_en_2`, `cell_en_3`, `cell_en_4`, `cell_en_5`, `cell_en_6`, `cell_en_7`
- `cell_en_8`, `cell_en_9`, `cell_en_10`, `cell_en_11`, `cell_en_12`, `cell_en_13`, `cell_en_14`, `cell_en_15`
- `ptr_0`, `ptr_1`, `ptr_2`, `ptr_3`, `ptr_4`, `ptr_5`, `ptr_6`, `ptr_7`
- `ptr_8`, `ptr_9`, `ptr_10`, `ptr_11`, `ptr_12`, `ptr_13`, `ptr_14`, `ptr_15`

If the DUT uses vector ports internally, the testbench must still save or expose every bit under the scalar names above. Do not rely only on CSV headers such as `code_i[0]`, `cell_en_o[0]`, or `ptr_o[0]`.

## Deliverables

Return the DUT Verilog-A file(s) and one Spectre testbench code block.


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=90n maxstep=0.1n
```

Required public waveform columns in `tran.csv`:

- `time`, `clk_i`, `rst_ni`, `ptr_0`, `ptr_1`, `ptr_2`, `ptr_3`, `ptr_4`
- `ptr_5`, `ptr_6`, `ptr_7`, `ptr_8`, `ptr_9`, `ptr_10`, `ptr_11`, `ptr_12`
- `ptr_13`, `ptr_14`, `ptr_15`, `cell_en_0`, `cell_en_1`, `cell_en_2`, `cell_en_3`, `cell_en_4`
- `cell_en_5`, `cell_en_6`, `cell_en_7`, `cell_en_8`, `cell_en_9`, `cell_en_10`, `cell_en_11`, `cell_en_12`
- `cell_en_13`, `cell_en_14`, `cell_en_15`, `code_0`, `code_1`, `code_2`, `code_3`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Reset-like input(s) `reset`, `rst_ni` must be asserted only for startup/explicit reset checks, then deasserted early enough and kept deasserted through the post-reset checking window.
- For active-low resets such as `rstb`, `rst_n`, or `rst_ni`, avoid a finite-width pulse that returns the reset node low after release; use a waveform that remains high during checking.
- Clock-like input(s) `clock` must provide enough valid edges after reset/enable for the checker to sample settled outputs.
- Sequential outputs are sampled shortly after clock edges, so drive outputs with stable held state variables and `transition()` targets rather than glitchy combinational expressions.
- Public stimulus nodes used by the reference harness include: `clk_i`, `rst_ni`.
