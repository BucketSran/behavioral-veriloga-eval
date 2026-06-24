# Agent-Visible Spec: vbr1_l1_ptat_ctat_reference_generator:dut

One-shot DUT-generation task for `PTAT/CTAT reference generator`.

## Agent-Visible Input

- `tb_ptat_ctat_reference_generator.scs`

## Required Output

- `ptat_ctat_reference_generator.va`

## Public Task Summary

- Level: `L1`
- Category: Bias Reference and Power Management
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

- `ptat_ctat_reference_generator.va` declares module `ptat_ctat_reference_generator` with positional ports: `clk`, `rst`, `vin`, `out`, `metric`.

## Public Testbench And Observable Contract

Public transient setting used by the release harness:

```spectre
tran tran stop=80n maxstep=0.5n
```

The release harness expects these exact public scalar observables:

- `clk`
- `rst`
- `vin`
- `out`
- `metric`

When this form generates a testbench, use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

## Public Behavioral Targets

- Treat vin as a voltage-coded temperature/control value in the 0-0.9 V range.
- Build opposing PTAT and CTAT internal trends; metric should expose a PTAT-like increasing branch.
- Combine PTAT and CTAT so out stays near a bounded reference around mid-scale instead of strongly tracking vin.
- Reset should initialize out near mid-scale and keep metric low until valid updates occur.
- Clamp out and metric to the public 0-0.9 V voltage-domain range.

## Output Contract

Return exactly one source artifact named `ptat_ctat_reference_generator.va`.
Do not include explanatory prose outside the source artifact contents.

## Task-Specific Public Description

### PTAT/CTAT reference generator (spec-to-va)

Write the Verilog-A behavioral module only.

Behavioral intent:

Generate PTAT and CTAT branch abstractions and combine them into a temperature-compensated voltage reference.

Module name: `ptat_ctat_reference_generator`.
Domain: pure voltage-domain behavioral Verilog-A.
Do not use current contributions, transistor-level devices, AC/noise analysis,
or KCL/KVL solving assumptions.

This is a voltage-domain macro-model task for bias/reference/power management behavior. Model observable startup, threshold, trim, hysteresis, droop, or recovery behavior with event-driven voltage state updates. Do not use branch currents, transistor devices, process-device equations, or true current-mode regulation loops.

Public port contract:

```verilog
module ptat_ctat_reference_generator(clk, rst, vin, out, metric);
input clk, rst, vin;
output out, metric;
electrical clk, rst, vin, out, metric;
```

Signal contract:

clk and rst are voltage-coded logic signals. vin is a normalized temperature-code voltage. out is the compensated reference voltage. metric exposes the PTAT branch trend as a public observable without revealing hidden checker code.

Saved waveform columns:

```text
clk rst vin out metric
```

Public transient contract:

```spectre
tran tran stop=80n maxstep=0.5n
```

## Modeling Constraints

Keep the implementation in the public voltage-domain behavioral Verilog-A task
scope. Do not emit hidden checker logic, private thresholds, private sample
windows, gold answers, current-domain device models, transistor-level circuits,
or AC/noise analysis assumptions unless they are explicitly part of the public
task contract.
