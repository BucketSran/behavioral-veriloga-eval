# Agent-Visible Spec: vbr1_l1_acquisition_limited_sample_and_hold:bugfix

One-shot bugfix task for `Acquisition-limited sample-and-hold`.

## Agent-Visible Input

- `dut_buggy.va`
- `tb_acquisition_limited_sample_hold.scs`
- `tb_acquisition_limited_sample_hold_buggy.scs`

## Required Output

- `dut_fixed.va`

## Public Task Summary

- Level: `L1`
- Category: Sampling and Analog Memory
- Domain: `voltage`
- Form: `bugfix`

## Public Observables

Saved signal names are part of the public contract: use actual top-level Spectre
nets connected to the DUT; do not rely on instance-qualified aliases.

- `sample`
- `rst`
- `vin`
- `vout`
- `metric`

If `time` is present, it is the implicit transient waveform axis.

## Form-Specific Requirements

- Repair the supplied buggy Verilog-A artifact while preserving the public module interface and artifact boundary.
- Use the buggy source plus the public intended behavior below; do not change the companion testbench contract.

## Public Interface To Preserve

- `dut_buggy.va` declares module `acquisition_limited_sample_hold` with positional ports: `sample`, `rst`, `vin`, `vout`, `metric`.
- `dut_fixed.va` declares module `acquisition_limited_sample_hold` with positional ports: `sample`, `rst`, `vin`, `vout`, `metric`.

## Public Testbench And Observable Contract

Public transient setting used by the release harness:

```spectre
tran tran stop=90n maxstep=250p
```

The release harness expects these exact public scalar observables:

- `sample`
- `rst`
- `vin`
- `vout`
- `metric`

When this form generates a testbench, use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

## Observed Mismatch Framing

The supplied buggy artifact violates one or more public functional contract under the release validation testbench.
Repair the observable behavior without renaming modules, changing ports, or weakening the public testbench contract.

Representative public mismatch scenarios:

| Scenario | Expected behavior | Faulty behavior to repair |
| --- | --- | --- |
| `sample` goes high while `vin` steps | `vout` moves toward `vin` with finite acquisition, not an instantaneous copy | `vout` jumps too aggressively or ignores the acquisition limit |
| longer sample-high window | `vout` settles closer to `vin` than in a shorter window | acquisition progress is not reflected in the held output |
| `sample` falls | `vout` holds the last acquired value with bounded droop/hold behavior | output keeps tracking the input after the hold edge |
| reset asserted | `vout` and metric return to the public initial state | reset does not clear the held/acquisition state |

## Output Contract

Return exactly one source artifact named `dut_fixed.va`.
Do not include explanatory prose outside the source artifact contents.

## Task-Specific Public Description

Write a pure voltage-domain Verilog-A model for an acquisition-limited sample-and-hold.

The model must represent finite acquisition bandwidth rather than an ideal instantaneous sampler:
- `sample` high opens a tracking/acquisition window.
- While tracking, `vout` moves toward the current `V(vin)` in discrete 1 ns acquisition updates.
- A falling `sample` edge freezes the last acquired value.
- High `rst` returns the held output to `vinit`.
- `metric` is high only while the model is actively tracking/acquiring.

Module name: `acquisition_limited_sample_hold`.
Domain: pure voltage-domain behavioral Verilog-A.
Do not use current contributions, transistor-level devices, AC/noise analysis, or KCL/KVL solving assumptions.

Public port contract:

```verilog
module acquisition_limited_sample_hold(sample, rst, vin, vout, metric);
```

Saved waveform columns:

```text
sample rst vin vout metric
```

Public transient contract:

```spectre
tran tran stop=90n maxstep=250p
```

## Modeling Constraints

Keep the implementation in the public voltage-domain behavioral Verilog-A task
scope. Do not emit hidden checker logic, private thresholds, private sample
windows, gold answers, current-domain device models, transistor-level circuits,
or AC/noise analysis assumptions unless they are explicitly part of the public
task contract.
