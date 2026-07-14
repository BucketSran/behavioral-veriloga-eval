# Programmable Stimulus Sequencer

## Task Contract

Implement the single-DUT Verilog-A artifact
`programmable_stimulus_sequencer.va` for a voltage-domain programmable stimulus
source. The model should generate ramp, chirp, and gated burst stimulus
segments from voltage-coded control inputs.

## Public Verilog-A Interface

The file `programmable_stimulus_sequencer.va` must define:

```verilog
module programmable_stimulus_sequencer(clk, rst, mode, gate, out, metric);
```

All ports are electrical. `clk`, `rst`, `mode`, and `gate` are voltage-coded
control inputs. `out` is the generated stimulus output, and `metric` reports
the active segment or status.

## Public Parameter Contract

- `tr = 80 ps`: transition smoothing time for voltage outputs.

## Required Behavior

Use low level near 0 V, high level near 0.9 V, and a 0.45 V decision threshold
for voltage-coded control signals. When reset is high, drive `out` near 0.45 V
and `metric` low. Otherwise:

- ramp mode, selected when `mode < 0.30 V`, drives a monotonic ramp segment
  from roughly 0.18 V toward 0.45 V and marks `metric` near 0.20 V;
- chirp mode, selected when `0.30 V <= mode < 0.60 V`, drives a sine segment
  centered near 0.45 V whose instantaneous frequency increases over the segment
  and marks `metric` near 0.50 V;
- burst mode, selected when `mode >= 0.60 V`, drives a gated PRBS-like burst
  between low and high stimulus levels while `gate` is high, returns `out` near
  0.45 V while `gate` is low, and marks `metric` near the burst or idle status.

The visible transient deck is a public verification scenario. Additional
validation may use different control schedules, so derive mode and gating
decisions from the voltage-coded inputs rather than from a particular stimulus
file.

## Modeling Constraints

Use voltage-domain behavioral Verilog-A. The DUT may use absolute transient
time to shape the ramp, chirp, and burst segments, but it must not emit a
Spectre testbench, validation logic, current contributions, `ddt()`, `idt()`,
transistor-level devices, AC/noise analysis, simulator-specific side channels,
or testbench-specific waveform tables.

## Output Contract

Return exactly one complete Verilog-A source artifact named
`programmable_stimulus_sequencer.va`. Do not include explanatory prose outside
the source artifact contents.
