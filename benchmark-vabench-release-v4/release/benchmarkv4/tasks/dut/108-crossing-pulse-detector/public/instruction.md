# Crossing Pulse Detector

## Task Contract

Implement the requested Verilog-A artifact for `Crossing Pulse Detector`.
- Form: `dut`
- Level: `L1`
- Category: `timing_primitive`
- Target artifact(s): `source_crossing_pulse_detector.va`

Implement `source_crossing_pulse_detector.va` in Verilog-A.

## Public Verilog-A Interface

```verilog
module source_crossing_pulse_detector(
    input  electrical sigin,
    output electrical sigout
);
```

## Public Parameter Contract

The public parameters declared by the target artifact are part of the contract and may be overridden by validation harnesses. Preserve their names, defaults, ranges, and meanings:

- `parameter real pulse_width = 4n from (0:inf);` in `source_crossing_pulse_detector.va`.
- `parameter real sigcrossing = 0.45;` in `source_crossing_pulse_detector.va`.
- `parameter real vlogic_high = 0.9;` in `source_crossing_pulse_detector.va`.
- `parameter real vlogic_low = 0.0;` in `source_crossing_pulse_detector.va`.
- `parameter real tdel = 1n from [0:inf);` in `source_crossing_pulse_detector.va`.
- `parameter real trise = 20p from (0:inf);` in `source_crossing_pulse_detector.va`.
- `parameter real tfall = 20p from (0:inf);` in `source_crossing_pulse_detector.va`.

## Required Behavior

This task asks for the `source_crossing_pulse_detector` behavioral DUT module,
not a testbench. The module emits a fixed-width pulse when `sigin`
crosses the configured threshold in either direction.

Support these public parameters and legal overrides:

| Parameter | Default | Unit / range | Contract |
| --- | ---: | --- | --- |
| `pulse_width` | `4 ns` | time, `(0:inf)` | Output high duration after a qualifying input crossing. |
| `sigcrossing` | `0.45` | V | Threshold for `sigin`. |
| `vlogic_high` | `0.9` | V | Output high level. |
| `vlogic_low` | `0.0` | V | Output low level. |
| `tdel` | `1 ns` | time, `[0:inf)` | Output transition delay. |
| `trise` | `20 ps` | time, `(0:inf)` | Output rise time. |
| `tfall` | `20 ps` | time, `(0:inf)` | Output fall time. |

Required observable behavior:

- Detect `sigin` crossings through `sigcrossing` in either direction.
- On each qualifying crossing, drive `sigout` high.
- Use a timer to return `sigout` low after `pulse_width`.
- Produce a pulse after each input crossing and return low between pulses.
- Drive `sigout` through smoothed voltage contributions.

Use voltage contributions only. Do not use current contributions, `ddt()`,
`idt()`, transistor-level devices, AC/noise analysis, validation logic, validation-only
test hooks, or simulator-specific side channels.

## Modeling Constraints

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one source artifact named `source_crossing_pulse_detector.va`.
