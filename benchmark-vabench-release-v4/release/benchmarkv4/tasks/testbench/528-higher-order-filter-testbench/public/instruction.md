# Clocked Cascaded Two-Pole Filter Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Clocked Cascaded Two-Pole Filter` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `higher_order_filter.va`:
  - Module `higher_order_filter` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `out` (output, electrical)
    - position 4: `metric` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `higher_order_filter` as `XDUT` with ordered public binding: clk=clk, rst=rst, vin=vin, out=out, metric=metric.

## Public Parameter Contract

- `higher_order_filter.tr` defaults to `1e-10` s; valid range: tr > 0; sets output transition smoothing.
- `higher_order_filter.gain` defaults to `1.8` V/V; valid range: gain > 0; sets input-deviation gain about 0.45 V common mode.
- `higher_order_filter.alpha` defaults to `0.18` unitless; valid range: 0 < alpha <= 1; sets each cascaded sampled low-pass update coefficient.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_COMMON_MODE_INITIAL_RESET`: exercise and make observable: Both cascaded states and observable out return to 0.45 V during initialization and active-high reset. Required traces: `time`, `rst`, `out`, `metric`.
- `P_GAINED_BOUNDED_TARGET`: exercise and make observable: Each eligible rising edge forms a rail-bounded target from gain times the input deviation around 0.45 V. Required traces: `time`, `clk`, `rst`, `vin`, `out`.
- `P_TWO_POLE_SAMPLED_SETTLING`: exercise and make observable: Out follows the second of two cascaded alpha-weighted sampled low-pass states and therefore settles more slowly than a single direct update. Required traces: `time`, `clk`, `vin`, `out`, `metric`.
- `P_LAG_METRIC`: exercise and make observable: Metric exposes the centered lag between the two cascaded states during settling and returns toward its baseline after convergence. Required traces: `time`, `clk`, `vin`, `out`, `metric`.
- `P_SIGNAL_RANGE`: exercise and make observable: The driven output remains within the public 0 V through 0.9 V signal range. Required traces: `time`, `out`.

The required trace names are: `time`, `clk`, `rst`, `vin`, `out`, `metric`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
