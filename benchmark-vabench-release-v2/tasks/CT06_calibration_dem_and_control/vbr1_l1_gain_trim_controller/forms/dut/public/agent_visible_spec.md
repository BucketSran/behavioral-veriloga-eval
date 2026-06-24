# Agent-Visible Spec: vbr1_l1_gain_trim_controller:dut

One-shot DUT-generation task for `Gain trim controller`.

## Agent-Visible Input

- `tb_gain_trim_controller_ref.scs`

## Required Output

- `gain_trim_controller.va`

## Public Task Summary

- Level: `L1`
- Category: Calibration, DEM, and Control
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

- `gain_trim_controller.va` declares module `gain_trim_controller` with positional ports: `clk`, `rst`, `meas`, `target`, `gain_ctrl`.

## Public Testbench And Observable Contract

Public transient setting used by the release harness:

```spectre
tran tran stop=620n maxstep=500p
```

The release harness expects these exact public scalar observables:

- `clk`
- `rst`
- `meas`
- `target`
- `gain_ctrl`

When this form generates a testbench, use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

## Output Contract

Return exactly one source artifact named `gain_trim_controller.va`.
Do not include explanatory prose outside the source artifact contents.

## Task-Specific Public Description

## Gain trim controller DUT

Write a pure voltage-domain Verilog-A module for a gain trim controller.

The DUT module is `gain_trim_controller` with ports `clk, rst, meas, target, gain_ctrl`. All ports are electrical; digital-control ports use 0/0.9 V logic levels.

Required behavior:
- Initialize and reset `gain_ctrl` to 0.30 V on rising `clk` while `rst` is high.
- When `meas` is below `target - 0.02`, increase the control by 0.05 V; when above `target + 0.02`, decrease it by 0.05 V.
- Hold inside the deadband, clamp to 0.05 V to 0.85 V, and drive through `transition()`.

Use voltage contributions only. Do not use current contributions, `ddt()`, or `idt()`.

Return exactly one complete Verilog-A file named `gain_trim_controller.va`.

## Modeling Constraints

Keep the implementation in the public voltage-domain behavioral Verilog-A task
scope. Do not emit hidden checker logic, private thresholds, private sample
windows, gold answers, current-domain device models, transistor-level circuits,
or AC/noise analysis assumptions unless they are explicitly part of the public
task contract.
