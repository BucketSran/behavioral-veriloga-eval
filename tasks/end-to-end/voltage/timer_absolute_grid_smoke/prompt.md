Write a Verilog-A module named `timer_absolute_grid_ref`.

# Task: timer_absolute_grid_smoke

## Objective

Create a behavioral timer source that toggles output on an absolute timer grid in Verilog-A and a minimal EVAS-compatible Spectre testbench.

## Specification

- **Module name**: `timer_absolute_grid_ref`
- **Ports** (all `electrical`, exactly as named): `VDD`, `VSS`, `clk_out`
- **Parameters**:
  - `tstart` (real, default `10n`)
  - `tstep` (real, default `10n`)
  - `tedge` (real, default `200p`)
- **Behavior**:
  - Start LOW at time 0.
  - On `@(initial_step)`, initialize `next_t = tstart`.
  - On every `@(timer(next_t))`, toggle the internal state and increment `next_t = next_t + tstep`.
  - Drive `clk_out` with `transition(...)` using the toggled state.
  - Under the gold testbench, `clk_out` should rise near `10.1 ns`, `30.1 ns`, `50.1 ns`, and `70.1 ns`.

## Testbench requirements

Create a minimal Spectre testbench that:
- Includes `timer_absolute_grid_ref.va` via `ahdl_include`
- Provides VDD=0.9V, VSS=0V
- Uses parameters tstart=10n, tstep=10n, tedge=200p
- Saves signal: `clk_out`
- Runs transient for 75ns

## Deliverable

Two files:
1. `timer_absolute_grid_ref.va` - the Verilog-A behavioral model
2. `tb_timer_absolute_grid_ref.scs` - the Spectre testbench

Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `clk_out`: output electrical
