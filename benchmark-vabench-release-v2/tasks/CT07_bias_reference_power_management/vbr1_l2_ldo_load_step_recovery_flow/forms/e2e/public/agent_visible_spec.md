# Agent-Visible Spec: vbr1_l2_ldo_load_step_recovery_flow:e2e

One-shot end-to-end task for `LDO load-step recovery flow`.

## Agent-Visible Input

- None

## Required Output

- `ldo_load_step_recovery_flow.va`
- `tb_ldo_load_step_recovery_flow.scs`

## Public Task Summary

- Level: `L2`
- Category: Bias Reference and Power Management
- Domain: `voltage`
- Form: `e2e`

## Public Observables

Saved signal names are part of the public contract: use actual top-level Spectre
nets connected to the DUT; do not rely on instance-qualified aliases.

- Inherited from the public harness

If `time` is present, it is the implicit transient waveform axis.

## L2 Background And Claim Boundary

This Level-2 row is a behavioral composition/flow task for LDO load-step recovery flow. It should expose intermediate state, multi-stage behavior, or a closed-loop relation through the public observables below.
Stay within the listed voltage-domain/event-driven contract. Do not use transistor-level devices, current-domain loads, AC/noise analysis, S-parameters, or hidden checker logic unless the public contract explicitly lists them.
Paper-facing claims for this row are limited to the public behavior checks below; do not broaden the task into full silicon implementation, layout, device physics, or unlisted performance metrics.

## Form-Specific Requirements

- Generate all target artifacts: `ldo_load_step_recovery_flow.va`, `tb_ldo_load_step_recovery_flow.scs`.
- The Spectre testbench must exercise the generated DUT/system through public observables; do not generate hidden checker logic.
- The generated Verilog-A file(s) `ldo_load_step_recovery_flow.va` must be co-located with the generated Spectre testbench.
- Include the generated DUT exactly with `ahdl_include "ldo_load_step_recovery_flow.va"` in the generated testbench.
- Use Spectre AHDL instance syntax with the instance name first and module name last: `XNAME (node1 node2 ...) module_name`.
- Never write module-first syntax such as `module_name instance_name (...)`; that is not the release Spectre testbench syntax.

## Public Verilog-A Interface

- `ldo_load_step_recovery_flow.va` declares module `ldo_load_step_recovery_flow` with positional ports: `clk`, `rst`, `vin`, `out`, `metric`, `load_mon`, `ctrl_mon`.

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
- `load_mon`
- `ctrl_mon`

When this form generates a testbench, use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Public stimulus/source nodes visible in the reference harness include:

- `clk`
- `rst`
- `vin`

## Public Spectre Testbench Scaffold

When this form generates a `.scs` testbench, use the following public skeleton shape. Fill in only the public stimulus details required by the task; do not copy or emit hidden checker logic.

```spectre
simulator lang=spectre
global 0
ahdl_include "ldo_load_step_recovery_flow.va"

XDUT (clk rst vin out metric load_mon ctrl_mon) ldo_load_step_recovery_flow

tran tran stop=80n maxstep=0.5n
save clk rst vin out metric load_mon ctrl_mon
```

Critical syntax rules:

- Every Verilog-A DUT/support file used by the testbench must have a literal `ahdl_include "<file>.va"` line in the `.scs` artifact.
- Spectre AHDL instances use instance-first/module-last syntax: `XNAME (node1 node2 ...) module_name`.
- Do not use module-first syntax such as `module_name instance_name (...)`.
- Keep saved names as plain scalar public observables, not instance-qualified aliases.

## Output Contract

Return exactly these source artifacts:

- `ldo_load_step_recovery_flow.va`
- `tb_ldo_load_step_recovery_flow.scs`

Do not include explanatory prose outside the source artifact contents.

## Task-Specific Public Description

### LDO load-step recovery flow (end-to-end)

Write both the Verilog-A behavioral module and a Spectre transient testbench.

Behavioral intent:

Compose a regulator macro model with repeated load-step disturbances and recovery-status observation.

Module name: `ldo_load_step_recovery_flow`.
Domain: pure voltage-domain behavioral Verilog-A.
Do not use current contributions, transistor-level devices, AC/noise analysis,
or KCL/KVL solving assumptions.

This is a voltage-domain macro-model task for bias/reference/power management behavior. Model observable startup, threshold, trim, hysteresis, droop, or recovery behavior with event-driven voltage state updates. Do not use branch currents, transistor devices, process-device equations, or true current-mode regulation loops.

Public port contract:

```verilog
module ldo_load_step_recovery_flow(clk, rst, vin, out, metric, load_mon, ctrl_mon);
input clk, rst, vin;
output out, metric, load_mon, ctrl_mon;
electrical clk, rst, vin, out, metric, load_mon, ctrl_mon;
```

Signal contract:

clk and rst are voltage-coded logic signals. vin is the public load-step stimulus. load_mon tracks the bounded load request seen by the regulator macro, ctrl_mon is an abstract voltage-domain pass/recovery control monitor, out is the regulator output after transient droop and recovery, and metric marks recovered regulation after each load transition. This remains a behavioral load-step recovery macro, not a transistor/pass-device LDO implementation.

Saved waveform columns:

```text
clk rst vin out metric load_mon ctrl_mon
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
