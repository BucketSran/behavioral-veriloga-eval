# Agent-Visible Spec: vbr1_l2_programmable_stimulus_sequencer:e2e

One-shot end-to-end task for `Programmable stimulus sequencer`.

## Agent-Visible Input

- None

## Required Output

- `programmable_stimulus_sequencer.va`
- `tb_programmable_stimulus_sequencer.scs`

## Public Task Summary

- Level: `L2`
- Category: Stimulus and Source Generators
- Domain: `voltage`
- Form: `e2e`

## Public Observables

Saved signal names are part of the public contract: use actual top-level Spectre
nets connected to the DUT; do not rely on instance-qualified aliases.

- Inherited from the public harness

If `time` is present, it is the implicit transient waveform axis.

## L2 Background And Claim Boundary

This Level-2 row is a reusable measurement/stimulus support flow for Programmable stimulus sequencer. It is certified as release content but remains outside the core circuit score denominator.
Stay within the listed voltage-domain/event-driven contract. Do not use transistor-level devices, current-domain loads, AC/noise analysis, S-parameters, or hidden checker logic unless the public contract explicitly lists them.
Paper-facing claims for this row are limited to support-flow behavior and must be reported separately from core analog/mixed-signal circuit-function coverage.

## Form-Specific Requirements

- Generate all target artifacts: `programmable_stimulus_sequencer.va`, `tb_programmable_stimulus_sequencer.scs`.
- The Spectre testbench must exercise the generated DUT/system through public observables; do not generate hidden checker logic.
- The generated Verilog-A file(s) `programmable_stimulus_sequencer.va` must be co-located with the generated Spectre testbench.
- Include the generated DUT exactly with `ahdl_include "programmable_stimulus_sequencer.va"` in the generated testbench.
- Use Spectre AHDL instance syntax with the instance name first and module name last: `XNAME (node1 node2 ...) module_name`.
- Never write module-first syntax such as `module_name instance_name (...)`; that is not the release Spectre testbench syntax.

## Public Verilog-A Interface

- `programmable_stimulus_sequencer.va` declares module `programmable_stimulus_sequencer` with positional ports: `clk`, `rst`, `mode`, `gate`, `out`, `metric`.

## Public Testbench And Observable Contract

Public transient setting used by the release harness:

```spectre
tran tran stop=90n maxstep=0.25n
```

The release harness expects these exact public scalar observables:

- `clk`
- `rst`
- `mode`
- `gate`
- `out`
- `metric`

When this form generates a testbench, use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Public stimulus/source nodes visible in the reference harness include:

- `clk`
- `rst`
- `mode`
- `gate`

## Public Spectre Testbench Scaffold

When this form generates a `.scs` testbench, use the following public skeleton shape. Fill in only the public stimulus details required by the task; do not copy or emit hidden checker logic.

```spectre
simulator lang=spectre
global 0
ahdl_include "programmable_stimulus_sequencer.va"

XDUT (clk rst mode gate out metric) programmable_stimulus_sequencer

tran tran stop=90n maxstep=0.25n
save clk rst mode gate out metric
```

Critical syntax rules:

- Every Verilog-A DUT/support file used by the testbench must have a literal `ahdl_include "<file>.va"` line in the `.scs` artifact.
- Spectre AHDL instances use instance-first/module-last syntax: `XNAME (node1 node2 ...) module_name`.
- Do not use module-first syntax such as `module_name instance_name (...)`.
- Keep saved names as plain scalar public observables, not instance-qualified aliases.

## Public L2 Behavior Contract

This support row is a programmable stimulus sequencer. It must expose multiple
stimulus modes and clean handoff between them:

1. Ramp mode:
   - With `mode` low, drive `out` as a monotonic ramp segment.
   - Keep the ramp bounded in the 0 V to 0.9 V signal range.

2. Swept sine or chirp mode:
   - With `mode` near midscale, drive a sine-like segment whose effective
     frequency increases over the segment.
   - Keep amplitude and common-mode continuous when entering this mode.

3. Burst/PRBS gate mode:
   - With `mode` high, use `gate` to enable and disable a burst or
     deterministic PRBS-like output segment.
   - When `gate` is low, hold or idle the output without uncontrolled jumps.

4. Mode continuity:
   - Mode transitions should avoid large discontinuities in output amplitude,
     phase, or common-mode.
   - Drive `metric` as a public mode/status observable.

The expected public relation is: mode schedule -> ramp, chirp, and gated burst
segments on `out`, with `metric` tracking the active schedule.

## Output Contract

Return exactly these source artifacts:

- `programmable_stimulus_sequencer.va`
- `tb_programmable_stimulus_sequencer.scs`

Do not include explanatory prose outside the source artifact contents.

## Task-Specific Public Description

### Programmable stimulus sequencer (end-to-end)

Write both the Verilog-A behavioral module and a Spectre transient testbench.

Behavioral intent:

Generate a programmable ramp, swept/chirp sine, and gated burst/PRBS stimulus schedule.

Module name: `programmable_stimulus_sequencer`.
Domain: pure voltage-domain behavioral Verilog-A.
Do not use current contributions, transistor-level devices, AC/noise analysis,
or KCL/KVL solving assumptions.

Public port contract:

```verilog
module programmable_stimulus_sequencer(clk, rst, mode, gate, out, metric);
input clk, rst, mode, gate;
output out, metric;
electrical clk, rst, mode, gate, out, metric;
```

Signal contract:

clk and rst are voltage-coded logic signals, low=0 V and high=0.9 V with threshold 0.45 V. mode selects ramp, sine, or burst/PRBS behavior. gate enables the burst segment. out is the generated stimulus waveform. metric is a voltage-coded segment-status observable.

Saved waveform columns:

```text
clk rst mode gate out metric
```

Public transient contract:

```spectre
tran tran stop=90n maxstep=0.25n
```

## Modeling Constraints

Keep the implementation in the public voltage-domain behavioral Verilog-A task
scope. Do not emit hidden checker logic, private thresholds, private sample
windows, gold answers, current-domain device models, transistor-level circuits,
or AC/noise analysis assumptions unless they are explicitly part of the public
task contract.
