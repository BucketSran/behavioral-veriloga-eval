# Agent-Visible Spec: vbr1_l1_peak_detector:dut

One-shot DUT-generation task for `Peak detector`.

## Agent-Visible Input

- `tb_peak_detector_ref.scs`

## Required Output

- `peak_detector.va`

## Public Task Summary

- Level: `L1`
- Category: Measurement Instrumentation Flows
- Domain: `voltage`
- Form: `dut`

## Public Observables

Saved signal names are part of the public contract: use actual top-level Spectre
nets connected to the DUT; do not rely on instance-qualified aliases.

- Inherited from the public harness

If `time` is present, it is the implicit transient waveform axis.

## Form-Specific Requirements

- Implement only the requested Verilog-A DUT artifact(s); do not generate a Spectre testbench in this form.
- Preserve the public module names, port order, parameters, and waveform observable names.

## Public Verilog-A Interface

- `peak_detector.va` declares module `peak_detector` with positional ports: `vin`, `rst`, `vout`.

## Public Testbench And Observable Contract

Public transient setting used by the release harness:

```spectre
tran tran stop=180n maxstep=500p
```

The release harness expects these exact public scalar observables:

- `vin`
- `rst`
- `vout`

When this form generates a testbench, use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

## Output Contract

Return exactly one source artifact named `peak_detector.va`.
Do not include explanatory prose outside the source artifact contents.

## Task-Specific Public Description


Write a pure voltage-domain Verilog-A module for a resettable peak detector.

The DUT module is `peak_detector` with ports `vin, rst, vout`. All ports are electrical; digital-control ports use 0/0.9 V logic levels.

Required behavior:
- Track the maximum observed `vin` value using a timer-sampled internal peak.
- High `rst` clears the peak to 0 V.
- Drive `vout` from the peak value through `transition()`.

Use voltage contributions only. Do not use current contributions, `ddt()`, or `idt()`.

Return exactly one complete Verilog-A file named `peak_detector.va`.

## Modeling Constraints

Keep the implementation in the public voltage-domain behavioral Verilog-A task
scope. Do not emit hidden checker logic, private thresholds, private sample
windows, gold answers, current-domain device models, transistor-level circuits,
or AC/noise analysis assumptions unless they are explicitly part of the public
task contract.
