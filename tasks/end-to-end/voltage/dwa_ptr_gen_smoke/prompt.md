Write a Verilog-A module named `dwa_ptr_gen` and one minimal EVAS-compatible Spectre testbench.

# Task: dwa_ptr_gen_smoke

## Objective

Create a pure voltage-domain Data Weighted Averaging (DWA) pointer generator. The testbench must
drive several input codes and expose a rotating 16-cell pointer and cell-enable window.

## DUT Contract

- Main module name: `dwa_ptr_gen`
- If you create an analog-to-4-bit helper module, name it `v2b_4b`.
- Ports, all `electrical`, exactly in this order:
  - Inputs: `clk_i`, `rst_ni`, `code_msb_i[3:0]`
  - Outputs: `cell_en_o[15:0]`, `ptr_o[15:0]`
- Parameters:
  - `vdd` real, default `0.9`
  - `vth` real, default `0.45`
  - `ptr_init` integer, default `0`
- Behavior:
  - Reset is active-low.
  - On reset, initialize the one-hot pointer to `ptr_init`.
  - On each rising `clk_i` edge after reset, decode the 4-bit input code and update:
    - `new_ptr = (old_ptr + code) % 16`
  - `ptr_o[*]` must be one-hot at the current pointer.
  - `cell_en_o[*]` must assert at least one selected cell after reset and represent the selected DWA window.
  - Use `@(cross(V(clk_i) - vth, +1))` and `transition(...)`.
  - Do not use current contributions, `ddt()`, or `idt()`.

## Testbench Contract

- Use a 0.9 V supply and 0 V reference.
- Generate a 100 MHz-class `clk_i` pulse clock and active-low `rst_ni` that deasserts early enough to leave several post-reset clock edges.
- Drive a sequence of 4-bit input codes that exercises pointer movement over multiple cells.
- If using `v2b_4b`, expose scalar code nodes `code_3`, `code_2`, `code_1`, `code_0`.
- Instantiate the DWA DUT by positional scalar ports.
- Save these exact scalar names:
  - `clk_i`, `rst_ni`
  - `cell_en_15` through `cell_en_0`
  - `ptr_15` through `ptr_0`
- Use the final transient setting listed in the Public Evaluation Contract below.

## Observable CSV Contract

The waveform CSV must expose the exact scalar names listed above. If the DUT uses vector ports
internally, the testbench must connect or save every bit as a scalar node.

## Deliverables

Return the complete artifact set:

1. `v2b_4b.va`, if you use a helper converter
2. `dwa_ptr_gen.va`
3. `tb_dwa_ptr_gen.scs`


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=100n maxstep=2n
```

Required public waveform columns in `tran.csv`:

- `clk_i`, `rst_ni`, `\`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Reset-like input(s) `reset`, `rst_ni` must be asserted only for startup/explicit reset checks, then deasserted early enough and kept deasserted through the post-reset checking window.
- For active-low reset inputs, avoid a finite-width pulse that returns the reset node low after release; use a waveform that remains high during checking.
- Enable-like input(s) `enable` must be in the enabled state during the post-reset checking window unless the task explicitly asks for disabled intervals.
- Clock-like input(s) `clock` must provide enough valid edges after reset/enable for the checker to sample settled outputs.
- Sequential outputs are sampled shortly after clock edges, so drive outputs with stable held state variables and `transition()` targets rather than glitchy combinational expressions.
- Public stimulus nodes used by the reference harness include: `clk_i`, `rst_ni`, `vin_node`.
