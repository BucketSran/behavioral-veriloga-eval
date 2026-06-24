# Agent-Visible Spec: vbr1_l1_lfsr_prbs_generator:bugfix

One-shot bugfix task for `PRBS stimulus/dither generator`.

## Agent-Visible Input

- `dut_buggy.va`
- `tb_prbs7_ref.scs`

## Required Output

- `dut_fixed.va`

## Public Task Summary

- Level: `L1`
- Category: Stimulus and Source Generators
- Domain: `voltage`
- Form: `bugfix`

## Public Observables

Saved signal names are part of the public contract: use actual top-level Spectre
nets connected to the DUT; do not rely on instance-qualified aliases.

- Inherited from the public harness

If `time` is present, it is the implicit transient waveform axis.

## Form-Specific Requirements

- Repair the supplied buggy Verilog-A artifact while preserving the public module interface and artifact boundary.
- Use the buggy source plus the public intended behavior below; do not change the companion testbench contract.

## Public Interface To Preserve

- `dut_buggy.va` declares module `prbs7_ref` with positional ports: `clk`, `rst_n`, `en`, `serial_out`, `state_0`, `state_1`, `state_2`, `state_3`, `state_4`, `state_5`, `state_6`.
- `dut_fixed.va` declares module `prbs7_ref` with positional ports: `clk`, `rst_n`, `en`, `serial_out`, `state_0`, `state_1`, `state_2`, `state_3`, `state_4`, `state_5`, `state_6`.

## Public Testbench And Observable Contract

Public transient setting used by the release harness:

```spectre
tran tran stop=120n maxstep=50p
```

The release harness expects these exact public scalar observables:

- `clk`
- `rst_n`
- `en`
- `serial_out`
- `state_0`
- `state_1`
- `state_2`
- `state_3`
- `state_4`
- `state_5`
- `state_6`

When this form generates a testbench, use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

## Observed Mismatch Framing

The supplied buggy artifact violates one or more public functional contract under the release validation testbench.
Repair the observable behavior without renaming modules, changing ports, or weakening the public testbench contract.

## Output Contract

Return exactly one source artifact named `dut_fixed.va`.
Do not include explanatory prose outside the source artifact contents.

## Task-Specific Public Description

# PRBS stimulus/dither generator Bugfix

Repair the supplied buggy Verilog-A implementation for the `PRBS stimulus/dither
generator`.

The fixed implementation must preserve the public module name and ports used by
the reference Spectre testbench. Domain: pure voltage-domain behavioral
Verilog-A. Do not use current contributions, transistor-level devices,
AC/noise analysis, or KCL/KVL solving assumptions.

## Modeling Constraints

Keep the implementation in the public voltage-domain behavioral Verilog-A task
scope. Do not emit hidden checker logic, private thresholds, private sample
windows, gold answers, current-domain device models, transistor-level circuits,
or AC/noise analysis assumptions unless they are explicitly part of the public
task contract.
