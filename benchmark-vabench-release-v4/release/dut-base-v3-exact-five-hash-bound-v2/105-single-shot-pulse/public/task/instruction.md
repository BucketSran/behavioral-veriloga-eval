# Single-Shot Pulse

## Task Contract

Implement the requested Verilog-A artifact for `Single Shot Pulse`.
- Form: `dut`
- Level: `L1`
- Category: `timing_primitive`
- Target artifact(s): `source_single_shot.va`

Implement `source_single_shot.va` in Verilog-A.

## Public Verilog-A Interface

```verilog
module source_single_shot(
    input  electrical vin,
    output electrical vout
);
```

## Public Parameter Contract

The public parameters declared by the target artifact are part of the contract and may be overridden by validation harnesses. Preserve their names, defaults, ranges, and meanings:

- `parameter real pulse_width = 10n from (0:inf);` in `source_single_shot.va`.
- `parameter real vlogic_high = 0.9;` in `source_single_shot.va`.
- `parameter real vlogic_low = 0.0;` in `source_single_shot.va`.
- `parameter real vtrans = 0.45;` in `source_single_shot.va`.
- `parameter real tdel = 1n from [0:inf);` in `source_single_shot.va`.
- `parameter real trise = 20p;` in `source_single_shot.va`.
- `parameter real tfall = 20p;` in `source_single_shot.va`.

## Required Behavior

This task asks for the `source_single_shot` behavioral DUT module, not a Spectre
testbench. The module is a voltage-domain one-shot pulse generator.

Support these public parameters and legal overrides:

| Parameter | Default | Unit / range | Contract |
| --- | ---: | --- | --- |
| `pulse_width` | `10 ns` | time, `(0:inf)` | Output high duration after a qualifying input edge. |
| `vlogic_high` | `0.9` | V | Output high level. |
| `vlogic_low` | `0.0` | V | Output low level. |
| `vtrans` | `0.45` | V | Rising-edge threshold for `vin`. |
| `tdel` | `1 ns` | time, `[0:inf)` | Output transition delay. |
| `trise` | `20 ps` | time, `(0:inf)` | Output rise time. |
| `tfall` | `20 ps` | time, `(0:inf)` | Output fall time. |

Required observable behavior:

- Detect rising `vin` crossings at `vtrans`.
- On each qualifying rising edge, drive `vout` high.
- Use a timer to return `vout` low after the configured pulse width.
- Generate one output pulse per input rising edge.
- Drive `vout` through smoothed voltage contributions.

Use voltage contributions only. Do not use current contributions, `ddt()`,
`idt()`, transistor-level devices, AC/noise analysis, validation logic, validation-only
test hooks, or simulator-specific side channels.

## Modeling Constraints

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The visible testbench is a public validation scenario; do not hard-code a particular stimulus table, transient stop time, or validation sample window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one source artifact named `source_single_shot.va`.
