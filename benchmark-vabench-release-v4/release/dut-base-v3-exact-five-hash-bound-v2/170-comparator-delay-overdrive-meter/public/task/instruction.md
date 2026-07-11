# Comparator Delay Overdrive Meter

## Task Contract

- Form: `dut`.
- Level: `L2`.
- Category: measurement/timing support primitive.
- Target artifact: `comparator_delay_overdrive_meter.va`.
- Role: clock-to-decision delay and overdrive meter for a supplied comparator support component.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module comparator_delay_overdrive_meter(vdd, vss, clk, vinp, vinn, outp, outn, delay_ps, overdrive_mv, polarity, valid);
```

`vdd`/`vss` define logic rails, `clk` is the comparator decision clock, `vinp`/`vinn` are sampled comparator inputs, `outp`/`outn` are comparator decision outputs, and `delay_ps`, `overdrive_mv`, `polarity`, and `valid` are measurement outputs.

## Public Parameter Contract

Provide overrideable parameter `tr = 20p` for report-output transition shaping. Use the midpoint between `vdd` and `vss` as the clock and decision threshold.

## Required Behavior

On each rising `clk` threshold crossing, store the current time and the absolute differential input overdrive. Arm one pending measurement. When either `outp` or `outn` rises through the decision threshold while armed, drive the voltage on `delay_ps` to the elapsed clock-to-output delay expressed in seconds and drive the voltage on `overdrive_mv` to the stored overdrive expressed in volts. The historical port suffixes name the human-facing diagnostic units; the evaluator converts these SI-valued electrical observables to picoseconds and millivolts. Set `polarity` high for an `outp` decision and low for an `outn` decision, assert `valid`, and disarm until the next clock edge. Hold reported values between measurements.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior. The comparator under measurement is supplied externally; do not include it in the returned artifact.

## Output Contract

Return exactly one complete Verilog-A source file named `comparator_delay_overdrive_meter.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
