# Edge Delay Line with Deglitch Window

## Task Contract

Implement one Verilog-A DUT artifact for `Edge Delay Line with Deglitch Window`.

- Target artifact: `edge_delay_line_deglitch.va`
- Public top module: `edge_delay_line_deglitch`
- Task level: `L1`
- Circuit category: `clock_timing`

## Public Verilog-A Interface

Declare module `edge_delay_line_deglitch` with positional electrical ports `vin, rst, enable, vout, edge_valid, rejected`. All ports are electrical.

`vin`, `rst`, and `enable` are voltage-coded inputs. `vout` is the delayed, deglitched output. `edge_valid` pulses when a qualified edge is emitted, and `rejected` pulses when a narrow glitch is rejected.

## Public Parameter Contract

Provide these overrideable public parameters:

- `vdd = 0.9 V`: logic-high output level
- `vss = 0.0 V`: logic-low output level
- `vth = 0.45 V`: logic threshold
- `tick = 250 ps`: internal scheduling tick
- `delay_ticks = 4`: qualified-edge delay in ticks
- `min_width_ticks = 3`: minimum stable input duration before an edge can qualify
- `tr = 100 ps`: output transition smoothing time

## Required Behavior

- Reset or a low `enable` clears the delayed output and all pending edge state.
- An input edge must remain stable for `min_width_ticks` timer ticks before it can be emitted.
- A qualified edge updates `vout` after an additional `delay_ticks` timer ticks.
- A pending edge that reverses before qualification is rejected and must not update `vout`.
- `edge_valid` pulses when a qualified delayed edge updates the output.
- `rejected` pulses when a narrow glitch is rejected.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not use current contributions, transistor-level devices, AC/noise analysis, random sources, table files, or topology-level assumptions. Use explicit initialization for stored state and smooth public voltage outputs with transition-style behavior.

Do not add extra ports, debug-only files, simulation decks, generated result files, or pass/fail flags.

## Output Contract

Return exactly one complete source artifact named `edge_delay_line_deglitch.va`.
