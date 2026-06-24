# Agent-Visible Spec: vbr1_l1_bang_bang_phase_detector:tb

One-shot testbench-generation task for `Bang-bang phase detector`.

## Agent-Visible Input

- `bbpd_data_edge_alignment_ref.va`

## Required Output

- `tb_bbpd_data_edge_alignment_ref.scs`

## Public Task Summary

- Level: `L1`
- Category: PLL Clock and Timing Systems
- Domain: `voltage`
- Form: `tb`

## Public Observables

Saved signal names are part of the public contract: use actual top-level Spectre
nets connected to the DUT; do not rely on instance-qualified aliases.

- `clk`
- `data`
- `up`
- `dn`
- `retimed_data`

If `time` is present, it is the implicit transient waveform axis.

## Form-Specific Requirements

- Generate only the Spectre transient testbench artifact(s); do not generate hidden checker logic.
- Instantiate the supplied/public DUT module(s), drive a public transient scenario, and save the required observables.
- The supplied DUT/support Verilog-A file(s) `bbpd_data_edge_alignment_ref.va` will be co-located with the generated testbench by the evaluation harness.
- Include it exactly with `ahdl_include "bbpd_data_edge_alignment_ref.va"` in the generated Spectre `.scs` netlist.
- Use Spectre AHDL instance syntax with the instance name first and module name last: `XNAME (node1 node2 ...) module_name`.
- Never write module-first syntax such as `module_name instance_name (...)`; that is not the release Spectre testbench syntax.

## Public DUT Interface To Instantiate

- `bbpd_data_edge_alignment_ref.va` declares module `bbpd_data_edge_alignment_ref` with positional ports: `vdd`, `vss`, `clk`, `data`, `up`, `dn`, `retimed_data`.

## Public Testbench And Observable Contract

Public transient setting used by the release harness:

```spectre
tran tran stop=170n maxstep=0.1n
```

The release harness expects these exact public scalar observables:

- `clk`
- `data`
- `up`
- `dn`
- `retimed_data`

When this form generates a testbench, use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Public stimulus/source nodes visible in the reference harness include:

- `vdd`
- `vss`
- `clk`
- `data`

## Public Spectre Testbench Scaffold

When this form generates a `.scs` testbench, use the following public skeleton shape. Fill in only the public stimulus details required by the task; do not copy or emit hidden checker logic.

```spectre
simulator lang=spectre
global 0
ahdl_include "bbpd_data_edge_alignment_ref.va"

Vvdd (vdd 0) vsource dc=0.9
Vvss (vss 0) vsource dc=0.0

XDUT (vdd vss clk data up dn retimed_data) bbpd_data_edge_alignment_ref

tran tran stop=170n maxstep=0.1n
save clk data up dn retimed_data
```

Critical syntax rules:

- Every Verilog-A DUT/support file used by the testbench must have a literal `ahdl_include "<file>.va"` line in the `.scs` artifact.
- Spectre AHDL instances use instance-first/module-last syntax: `XNAME (node1 node2 ...) module_name`.
- Do not use module-first syntax such as `module_name instance_name (...)`.
- Keep saved names as plain scalar public observables, not instance-qualified aliases.

## Output Contract

Return exactly one source artifact named `tb_bbpd_data_edge_alignment_ref.scs`.
Do not include explanatory prose outside the source artifact contents.

## Task-Specific Public Description

## Bang-bang phase detector Testbench Companion

Write a Spectre transient testbench for the `Bang-bang phase detector` behavioral
Verilog-A release task. This is the testbench-generation companion for an
already materialized end-to-end task.

The testbench should instantiate the same behavioral DUT or system module used
by the corresponding end-to-end form, drive the public transient scenario, save
the observable waveform or metric signals, and preserve the EVAS/Spectre
validation contract.

Domain: pure voltage-domain behavioral Verilog-A.

Public requirements:

- include a transient `tran` analysis
- save the public observables needed by the checker
- include or instantiate the Verilog-A behavioral module under test
- avoid transistor-level devices, AC/noise analysis, and current-domain
  solver assumptions

## Modeling Constraints

Keep the implementation in the public voltage-domain behavioral Verilog-A task
scope. Do not emit hidden checker logic, private thresholds, private sample
windows, gold answers, current-domain device models, transistor-level circuits,
or AC/noise analysis assumptions unless they are explicitly part of the public
task contract.
