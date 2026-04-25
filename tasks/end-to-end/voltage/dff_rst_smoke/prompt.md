Write a Verilog-A module named `dff_rst`.

# Task: dff_rst_smoke

## Objective

Create a D flip-flop with synchronous reset behavioral model in Verilog-A and a minimal EVAS-compatible Spectre testbench.

## Specification

- **Module name**: `dff_rst`
- **Ports** (all `electrical`, exactly as named): `vdd`, `vss`, `d`, `clk`, `rst`, `q`, `qb`
- **Parameters**: `tedge` (real, default 10p)
- **Behavior**:
  - On rising edge of `clk`:
    - If `rst` is HIGH, `q` goes LOW (reset)
    - Otherwise, `q` samples `d`
  - `qb` is always the complement of `q`
  - Threshold at `(vdd - vss)/2` for level detection
- **Output**: use `transition()` only. No `idt`, `ddt`, or `I() <+`.

## Testbench requirements

Create a minimal Spectre testbench that:
- Includes `dff_rst.va` via `ahdl_include`
- Provides vdd=1.8V, vss=0V
- Generates 1GHz clock (period=2ns)
- Tests D sampling and synchronous reset
- Saves signals: `d`, `clk`, `rst`, `q`, `qb`
- Runs transient for 20ns

## Deliverable

Two files:
1. `dff_rst.va` - the Verilog-A behavioral model
2. `tb_dff_rst.scs` - the Spectre testbench

Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `D`: input electrical
- `CLK`: input electrical
- `RST`: input electrical
- `Q`: output electrical
- `QB`: output electrical


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=20n maxstep=50p
```

Required public waveform columns in `tran.csv`:

- `time`, `d`, `clk`, `rst`, `q`, `qb`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Reset-like input(s) `rst`, `reset` must be asserted only for startup/explicit reset checks, then deasserted early enough and kept deasserted through the post-reset checking window.
- For active-low resets such as `rstb`, `rst_n`, or `rst_ni`, avoid a finite-width pulse that returns the reset node low after release; use a waveform that remains high during checking.
- Clock-like input(s) `clk`, `clock` must provide enough valid edges after reset/enable for the checker to sample settled outputs.
- Sequential outputs are sampled shortly after clock edges, so drive outputs with stable held state variables and `transition()` targets rather than glitchy combinational expressions.
- Public stimulus nodes used by the reference harness include: `vdd`, `vss`, `clk`, `d`, `rst`.
