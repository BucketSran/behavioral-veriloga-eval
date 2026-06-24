# Agent-Visible Spec: vbr1_l1_vco_phase_integrator:dut

One-shot DUT-generation task for `VCO phase integrator`.

## Agent-Visible Input

- `tb_vco_phase_integrator_ref.scs`

## Required Output

- `vco_phase_integrator.va`

## Public Task Summary

- Level: `L1`
- Category: PLL Clock and Timing Systems
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

- `vco_phase_integrator.va` declares module `vco_phase_integrator` with positional ports: `vctrl`, `phase`, `clk`.

## Public Testbench And Observable Contract

Public transient setting used by the release harness:

```spectre
tran tran stop=180n maxstep=500p
```

The release harness expects these exact public scalar observables:

- `vctrl`
- `phase`
- `clk`

When this form generates a testbench, use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

## Output Contract

Return exactly one source artifact named `vco_phase_integrator.va`.
Do not include explanatory prose outside the source artifact contents.

## Task-Specific Public Description

## VCO Phase Integrator DUT

Write a pure voltage-domain Verilog-A module for a voltage-controlled VCO phase integrator with periodic phase updates.

The DUT module is `vco_phase_integrator` with ports `vctrl, phase, clk`. All ports are electrical; digital-control ports use 0/0.9 V logic levels.

Required behavior:
- Use a 1 ns timer update and increment phase by `0.03 + 0.09 * V(vctrl)` at each update.
- Wrap phase at 1.0 and toggle `clk` on each wrap.
- Drive both `phase` and `clk` through `transition()`.

Use voltage contributions only. Do not use current contributions, `ddt()`, or `idt()`.

Return exactly one complete Verilog-A file named `vco_phase_integrator.va`.

## Modeling Constraints

Keep the implementation in the public voltage-domain behavioral Verilog-A task
scope. Do not emit hidden checker logic, private thresholds, private sample
windows, gold answers, current-domain device models, transistor-level circuits,
or AC/noise analysis assumptions unless they are explicitly part of the public
task contract.
