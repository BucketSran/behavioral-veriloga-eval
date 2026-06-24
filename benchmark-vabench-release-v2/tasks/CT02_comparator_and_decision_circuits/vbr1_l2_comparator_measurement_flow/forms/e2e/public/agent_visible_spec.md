# Agent-Visible Spec: vbr1_l2_comparator_measurement_flow:e2e

One-shot end-to-end task for `Single-ramp comparator offset measurement flow`.

## Agent-Visible Input

- None

## Required Output

- `comparator_offset_search_ref.va`
- `tb_comparator_offset_search_ref.scs`

## Public Task Summary

- Level: `L2`
- Category: Comparator and Decision Circuits
- Domain: `voltage`
- Form: `e2e`

## Public Observables

Saved signal names are part of the public contract: use actual top-level Spectre
nets connected to the DUT; do not rely on instance-qualified aliases.

- Inherited from the public harness

If `time` is present, it is the implicit transient waveform axis.

## L2 Background And Claim Boundary

This Level-2 row is a behavioral composition/flow task for Single-ramp comparator offset measurement flow. It should expose intermediate state, multi-stage behavior, or a closed-loop relation through the public observables below.
Stay within the listed voltage-domain/event-driven contract. Do not use transistor-level devices, current-domain loads, AC/noise analysis, S-parameters, or hidden checker logic unless the public contract explicitly lists them.
Paper-facing claims for this row are limited to the public behavior checks below; do not broaden the task into full silicon implementation, layout, device physics, or unlisted performance metrics.

## Form-Specific Requirements

- Generate all target artifacts: `comparator_offset_search_ref.va`, `tb_comparator_offset_search_ref.scs`.
- The Spectre testbench must exercise the generated DUT/system through public observables; do not generate hidden checker logic.
- The generated Verilog-A file(s) `comparator_offset_search_ref.va` must be co-located with the generated Spectre testbench.
- Include the generated DUT exactly with `ahdl_include "comparator_offset_search_ref.va"` in the generated testbench.
- Use Spectre AHDL instance syntax with the instance name first and module name last: `XNAME (node1 node2 ...) module_name`.
- Never write module-first syntax such as `module_name instance_name (...)`; that is not the release Spectre testbench syntax.

## Public Verilog-A Interface

- `comparator_offset_search_ref.va` declares module `comparator_offset_search_ref` with positional ports: `vdd`, `vss`, `inp`, `inn`, `outp`, `trip_v`, `offset_est`, `valid`.

## Public Testbench And Observable Contract

Public transient setting used by the release harness:

```spectre
tran tran stop=100n maxstep=50p errpreset=conservative
```

The release harness expects these exact public scalar observables:

- `inp`
- `inn`
- `outp`
- `trip_v`
- `offset_est`
- `valid`

When this form generates a testbench, use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Public stimulus/source nodes visible in the reference harness include:

- `vdd`
- `vss`
- `inn`
- `inp`

## Public Spectre Testbench Scaffold

When this form generates a `.scs` testbench, use the following public skeleton shape. Fill in only the public stimulus details required by the task; do not copy or emit hidden checker logic.

```spectre
simulator lang=spectre
global 0
ahdl_include "comparator_offset_search_ref.va"

Vvdd (vdd 0) vsource dc=0.9
Vvss (vss 0) vsource dc=0.0

XDUT (vdd vss inp inn outp trip_v offset_est valid) comparator_offset_search_ref

tran tran stop=100n maxstep=50p errpreset=conservative
save inp inn outp trip_v offset_est valid
```

Critical syntax rules:

- Every Verilog-A DUT/support file used by the testbench must have a literal `ahdl_include "<file>.va"` line in the `.scs` artifact.
- Spectre AHDL instances use instance-first/module-last syntax: `XNAME (node1 node2 ...) module_name`.
- Do not use module-first syntax such as `module_name instance_name (...)`.
- Keep saved names as plain scalar public observables, not instance-qualified aliases.

## Public L2 Behavior Contract

This row is a single-ramp comparator offset measurement flow. It is not only a
bare comparator; it must expose the measurement latch that captures the first
trip point.

1. Comparator decision:
   - Hold `inn` at 0.500 V.
   - Ramp `inp` from below to above the expected trip point.
   - With `vos = 5m`, drive `outp` low before `V(inp) - V(inn) > vos` and high
     after the first rising trip.

2. Measurement latch:
   - Before the first trip, keep `valid` low.
   - On the first rising trip only, latch `trip_v = V(inp)` and
     `offset_est = V(inp) - V(inn)`.
   - After `valid` goes high, hold `trip_v` and `offset_est` stable instead of
     letting them continue to follow the ramp.

3. Public stimulus shape:
   - Use a monotonic `inp` ramp from about 0.490 V to about 0.520 V with
     `inn = 0.500 V`.
   - The expected public relation is that the first `outp` transition, `valid`
     assertion, `trip_v`, and `offset_est` all point to the same near-5 mV
     offset measurement.

Use top-level `@(cross(..., +1))` event control for the trip detector and
`transition()` for rail outputs.

## Output Contract

Return exactly these source artifacts:

- `comparator_offset_search_ref.va`
- `tb_comparator_offset_search_ref.scs`

Do not include explanatory prose outside the source artifact contents.

## Task-Specific Public Description

Write a pure voltage-domain Verilog-A single-ramp comparator offset
measurement flow. This is an L2 task: the generated artifact must include both
the comparator decision and measurement observables that latch the detected
trip voltage and offset estimate during one controlled transient input ramp.

Module name: `comparator_offset_search_ref`.

Requirements:

1. Ports, in order: `vdd`, `vss`, `inp`, `inn`, `outp`, `trip_v`, `offset_est`, `valid`
2. Built-in offset parameter `vos = 5m`
3. Comparator output `outp` switches high when `V(inp, vss) - V(inn, vss) > vos`
4. On the rising threshold crossing, latch `trip_v = V(inp, vss)` and `offset_est = V(inp, vss) - V(inn, vss)`
5. Drive `valid` low before the first rising crossing and high after the measurement latches
6. Keep `trip_v` and `offset_est` stable after `valid` goes high
7. Use portable Verilog-A event constructs: `@(initial_step)`, directional `cross()` events, and `transition()`
8. The benchmark testbench performs a single ramp of `inp` from 0.490 V toward 0.520 V with `inn = 0.500 V`; the expected latched trip voltage is near 0.505 V and the expected offset estimate is near 0.005 V

Ports:
- `vdd`: electrical
- `vss`: electrical
- `inp`: electrical
- `inn`: electrical
- `outp`: electrical (power rail)
- `trip_v`: electrical measurement voltage
- `offset_est`: electrical measurement voltage
- `valid`: electrical validity flag on the power rail

## Modeling Constraints

Keep the implementation in the public voltage-domain behavioral Verilog-A task
scope. Do not emit hidden checker logic, private thresholds, private sample
windows, gold answers, current-domain device models, transistor-level circuits,
or AC/noise analysis assumptions unless they are explicitly part of the public
task contract.
