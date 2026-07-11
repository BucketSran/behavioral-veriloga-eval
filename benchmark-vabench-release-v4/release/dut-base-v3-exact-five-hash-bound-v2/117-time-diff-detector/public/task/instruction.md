# Time Difference Detector

## Task Contract

Implement the requested Verilog-A artifact for `Time Diff Detector`.
- Form: `dut`
- Level: `L1`
- Category: `mixed_signal`
- Target artifact(s): `time_diff_detector.va`

Implement the Verilog-A DUT `time_diff_detector.va` for a clocked timing detector that reports the previous cycle's input edge-time difference as a bounded voltage.

This is a single-DUT measurement utility. The DUT should derive timing from threshold crossings in the provided analog waveforms rather than from fixed testbench timestamps.

## Public Verilog-A Interface

Provide `module time_diff_detector(clk, vinp, vinn, vout);` with electrical inputs `clk`, `vinp`, `vinn` and electrical output `vout`.

## Public Parameter Contract

Expose `vdd = 0.9`, `vth_clk = 0.45`, `vth_in = 0.45`, `td = 0`, `tr = 1p`, and `scale = 1e9`. Testbenches may override these parameters.

## Required Behavior

On each rising `clk` crossing of `vth_clk`, output the stored difference
between the first rising `vinp` crossing and first rising `vinn` crossing
captured in the previous clock window. A window is valid only when both input
edges are captured. If either input edge is absent in the previous window, hold
the previous `vout` value unchanged while rearming detection for the next
window. For a valid window, scale the time difference by `scale`, clip the
output to `[-vdd, vdd]`, then rearm detection for the next window.

## Modeling Constraints

Use `cross`-style event detection and `transition(vout_value, td, tr)` or equivalent Spectre-compatible event behavior. Do not accumulate multiple edges in one clock window or fail to rearm after each clock event.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The visible testbench is a public validation scenario; do not hard-code a particular stimulus table, transient stop time, or validation sample window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Submit only the completed Verilog-A module in `time_diff_detector.va`.
