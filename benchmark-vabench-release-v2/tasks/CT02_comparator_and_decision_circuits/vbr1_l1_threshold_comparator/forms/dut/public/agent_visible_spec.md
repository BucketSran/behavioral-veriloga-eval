# Agent-Visible Spec: vbr1_l1_threshold_comparator:dut

One-shot DUT-generation task for `Threshold comparator`.

## Agent-Visible Input

- `tb_comparator_ref.scs`

## Required Output

- `comparator.va`

## Public Task Summary

- Level: `L1`
- Category: Comparator and Decision Circuits
- Domain: `voltage`
- Form: `dut`

## Public Observables

Saved signal names are part of the public contract: use actual top-level Spectre
nets connected to the DUT; do not rely on instance-qualified aliases.

- `vinp`
- `vinn`
- `out_p`

If `time` is present, it is the implicit transient waveform axis.

## Form-Specific Requirements

- Implement only the requested Verilog-A DUT artifact(s); do not generate a Spectre testbench in this form.
- Preserve the public module names, port order, parameters, and waveform observable names.

## Public Verilog-A Interface

- `comparator.va` declares module `comparator` with positional ports: `VDD`, `VSS`, `VINP`, `VINN`, `OUT_P`.

## Public Testbench And Observable Contract

Public transient setting used by the release harness:

```spectre
tran tran stop=30n maxstep=0.1n
```

The release harness expects these exact public scalar observables:

- `vinp`
- `vinn`
- `out_p`

When this form generates a testbench, use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

## Output Contract

Return exactly one source artifact named `comparator.va`.
Do not include explanatory prose outside the source artifact contents.

## Task-Specific Public Description

# Threshold comparator DUT

Write the Verilog-A DUT artifact(s) for `Threshold comparator`.

This is a function-checked DUT task, not a generic companion wrapper. The
public contract below defines the exact module interface, voltage-domain
behavior, and waveform observables used by the release checker.

Domain: pure voltage-domain behavioral Verilog-A.

## Module Contract

- Declaration: `comparator(vdd, vss, vinp, vinn, out_p)`

Ports:

- `vdd`, `vss`: electrical supply rails
- `vinp`, `vinn`: input electrical differential pair
- `out_p`: output electrical single-ended decision

## Behavioral Contract

- drive `out_p` high when `V(vinp) > V(vinn)` by a visible margin
- drive `out_p` low when `V(vinp) < V(vinn)` by a visible margin
- respond to both rising and falling zero-differential crossings, not only a
  single low-to-high threshold event
- use rail-referenced output levels and finite `transition(...)` edges

## Public Evaluation Observables

The companion validation testbench saves these waveform columns:

- `vinp`
- `vinn`
- `out_p`

## Modeling Constraints

Keep the implementation in the public voltage-domain behavioral Verilog-A task
scope. Do not emit hidden checker logic, private thresholds, private sample
windows, gold answers, current-domain device models, transistor-level circuits,
or AC/noise analysis assumptions unless they are explicitly part of the public
task contract.
