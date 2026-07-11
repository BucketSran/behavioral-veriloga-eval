# Peak Detector

## Task Contract

Implement the requested Verilog-A artifact for `Peak Detector`.
- Form: `dut`
- Level: `L1`
- Category: `measurement_instrumentation_flows`
- Target artifact(s): `peak_detector.va`

Implement `peak_detector.va` in Verilog-A.

## Public Verilog-A Interface

```verilog
module peak_detector(vin, rst, vout);
```

Inputs:

- `vin`: electrical input to measure.
- `rst`: electrical reset input using 0/0.9 V logic levels.

Outputs:

- `vout`: electrical output holding the measured peak.

## Public Parameter Contract

| Parameter | Default | Contract |
| --- | ---: | --- |
| `vth` | `0.45 V` | Reset threshold for `rst`. |
| `tr` | `500 ps` | Rise/fall smoothing for `vout`. |

## Required Behavior

Write a pure voltage-domain resettable peak detector. The model should sample
`vin` on a 500 ps timer, retain the maximum sampled value, and drive `vout`
from that retained peak.

Required observable behavior:

- Initialize the retained peak to 0 V.
- While `rst` is above `vth`, clear the retained peak to 0 V.
- While reset is inactive, update the retained peak when a sampled `vin` value
  is larger than the current peak.
- Hold the first peak, clear it on reset, and update to a larger later peak.

Use voltage contributions only. Smooth `vout` with `transition()`. Do not
generate a the simulator example harness, waveform files, validation artifacts,
transistor-level devices, current contributions, `ddt()`, or `idt()`.

## Modeling Constraints

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The public example harness is a public validation scenario; do not hard-code a particular stimulus table, runtime horizon, or sampling window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete Verilog-A file named `peak_detector.va`.
