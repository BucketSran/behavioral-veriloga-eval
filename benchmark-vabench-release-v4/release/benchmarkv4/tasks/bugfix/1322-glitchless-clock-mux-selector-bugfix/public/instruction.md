# Glitchless Clock Mux Selector Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `glitchless_clock_mux_selector.va`:
  - Module `glitchless_clock_mux_selector` (entry)
    - position 0: `clk_a` (inout, electrical)
    - position 1: `clk_b` (inout, electrical)
    - position 2: `sel` (inout, electrical)
    - position 3: `rst` (inout, electrical)
    - position 4: `enable` (inout, electrical)
    - position 5: `clk_out` (inout, electrical)
    - position 6: `switch_metric` (inout, electrical)
    - position 7: `valid` (inout, electrical)

## Public Parameter Contract

- `glitchless_clock_mux_selector.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `glitchless_clock_mux_selector.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `glitchless_clock_mux_selector.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `glitchless_clock_mux_selector.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `glitchless_clock_mux_selector.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `glitchless_clock_mux_selector.tick` defaults to `200p from (0:inf)`; valid range: finite; overrides tick.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_DISABLED_DRIVE`: restore: On reset or when disabled, drive `clk_out`, `switch_metric`, and `valid` low. Required traces: `time`, `clk_a`, `clk_b`, `sel`, `rst`, `enable`, `clk_out`, `switch_metric`, `valid`.
- `P_ROUTE_CLK_A_WHEN_SEL_IS`: restore: Route `clk_a` when `sel` is low and `clk_b` when `sel` is high. Required traces: `time`, `clk_a`, `clk_b`, `sel`, `rst`, `enable`, `clk_out`, `switch_metric`, `valid`.
- `P_WHEN_SEL_CHANGES_WAIT_UNTIL_BOTH`: restore: When `sel` changes, wait until both input clocks are low before changing the active source. Required traces: `time`, `clk_a`, `clk_b`, `sel`, `rst`, `enable`, `clk_out`, `switch_metric`, `valid`.
- `P_EXPOSE_A_SWITCH_EVENT_ON_SWITCH`: restore: Expose a switch event on `switch_metric` for one output cycle after the selected source changes. Required traces: `time`, `clk_a`, `clk_b`, `sel`, `rst`, `enable`, `clk_out`, `switch_metric`, `valid`.
- `P_ASSERT_VALID_AFTER_THE_SELECTED_SOURCE`: restore: Assert `valid` after the selected source has produced one clean output edge. Required traces: `time`, `clk_a`, `clk_b`, `sel`, `rst`, `enable`, `clk_out`, `switch_metric`, `valid`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `glitchless_clock_mux_selector.va`.
Every supplied `.va` file is editable; do not add or omit files.
