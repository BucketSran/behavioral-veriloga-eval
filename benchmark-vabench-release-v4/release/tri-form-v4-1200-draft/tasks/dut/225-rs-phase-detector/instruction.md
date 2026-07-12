# RS Phase Detector

## Task Contract

Implement `rs_phase_detector.va` as an RS-latch style phase detector for voltage-coded reference and feedback clocks.

## Public Verilog-A Interface

Use this module signature:

```verilog
module rs_phase_detector(ref, fb, up, down);
```

All ports are scalar `electrical` nodes. `ref` and `fb` are voltage-coded clock inputs. `up` and `down` are complementary voltage-coded latch outputs.

## Public Parameter Contract

- `vdd`: high level for outputs and threshold reference, default `1.2`.
- `tdel`: output transition delay, default `10p`.
- `tr`: output rise time, default `10p`.
- `tf`: output fall time, default `10p`.

## Required Behavior

- Detect rising `ref` and `fb` crossings at `vdd/2`.
- A rising `ref` edge sets the latch state so `up` is high and `down` is low.
- A rising `fb` edge resets the latch state so `up` is low and `down` is high.
- Hold the most recent latch state between qualifying input edges.
- Initialize to the reset state with `up` low and `down` high.

## Modeling Constraints

Use voltage contributions only. Do not use current contributions, transistor-level devices, AC/noise analysis, checker logic, out-of-band test hooks, or simulator side channels.

## Output Contract

Return exactly one source artifact named `rs_phase_detector.va`.
