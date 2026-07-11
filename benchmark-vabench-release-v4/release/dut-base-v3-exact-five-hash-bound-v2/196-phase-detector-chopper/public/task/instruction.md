# Phase Detector Chopper

## Task Contract

- Form: `dut`.
- Level: `L1`.
- Category: mixer/phase-detector primitive.
- Target artifact: `phase_detector_chopper.va`.
- Role: LO-polarity controlled RF sign chopper.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module phase_detector_chopper(vlocal_osc, vin_rf, vif);
```

`vlocal_osc` is the local oscillator control input, `vin_rf` is the analog RF input, and `vif` is the chopped IF output. All ports are electrical.

## Public Parameter Contract

Provide overrideable parameter `gain = 1.25`.

## Required Behavior

Drive `vif` as `gain*vin_rf` when `vlocal_osc` is positive and as `-gain*vin_rf` otherwise. The output should track input changes continuously without clocked state.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `phase_detector_chopper.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
