# Agent-Visible Spec: vbr1_l2_complete_calibration_loop:e2e

One-shot end-to-end task for `Complete calibration loop`.

## Agent-Visible Input

- None

## Required Output

- `complete_calibration_loop.va`
- `tb_complete_calibration_loop.scs`

## Public Task Summary

- Level: `L2`
- Category: Calibration, DEM, and Control
- Domain: `voltage`
- Form: `e2e`

## Public Observables

Saved signal names are part of the public contract: use actual top-level Spectre
nets connected to the DUT; do not rely on instance-qualified aliases.

- Inherited from the public harness

If `time` is present, it is the implicit transient waveform axis.

## L2 Background And Claim Boundary

This Level-2 row is a behavioral composition/flow task for Complete calibration loop. It should expose intermediate state, multi-stage behavior, or a closed-loop relation through the public observables below.
Stay within the listed voltage-domain/event-driven contract. Do not use transistor-level devices, current-domain loads, AC/noise analysis, S-parameters, or hidden checker logic unless the public contract explicitly lists them.
Paper-facing claims for this row are limited to the public behavior checks below; do not broaden the task into full silicon implementation, layout, device physics, or unlisted performance metrics.

## Form-Specific Requirements

- Generate all target artifacts: `complete_calibration_loop.va`, `tb_complete_calibration_loop.scs`.
- The Spectre testbench must exercise the generated DUT/system through public observables; do not generate hidden checker logic.
- The generated Verilog-A file(s) `complete_calibration_loop.va` must be co-located with the generated Spectre testbench.
- Include the generated DUT exactly with `ahdl_include "complete_calibration_loop.va"` in the generated testbench.
- Use Spectre AHDL instance syntax with the instance name first and module name last: `XNAME (node1 node2 ...) module_name`.
- Never write module-first syntax such as `module_name instance_name (...)`; that is not the release Spectre testbench syntax.

## Public Verilog-A Interface

- `complete_calibration_loop.va` declares module `complete_calibration_loop` with positional ports: `clk`, `rst`, `vin`, `out`, `metric`, `trim_mon`, `residual_mon`.

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
- `trim_mon`
- `residual_mon`

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
ahdl_include "complete_calibration_loop.va"

XDUT (clk rst vin out metric trim_mon residual_mon) complete_calibration_loop

tran tran stop=80n maxstep=0.5n
save clk rst vin out metric trim_mon residual_mon
```

Critical syntax rules:

- Every Verilog-A DUT/support file used by the testbench must have a literal `ahdl_include "<file>.va"` line in the `.scs` artifact.
- Spectre AHDL instances use instance-first/module-last syntax: `XNAME (node1 node2 ...) module_name`.
- Do not use module-first syntax such as `module_name instance_name (...)`.
- Keep saved names as plain scalar public observables, not instance-qualified aliases.

## Public L2 Behavior Contract

This row is a complete calibration loop from error stimulus to correction and
convergence metric:

1. Error stimulus:
   - Treat `vin` as the public raw error or offset stimulus around the 0.45 V
     center point.
   - The testbench should include positive and negative error excursions and a
     reset interval.

2. Negative-feedback correction:
   - Drive `out` as the corrected output after the internal controller and
     actuator response.
   - Large positive input error should push the correction in the opposite
     direction from large negative input error.
   - Keep the correction bounded in the 0 V to 0.9 V signal range.

3. Convergence metric:
   - Drive `metric` as a public convergence or residual-error indicator.
   - The metric should improve when the loop has reduced the visible error and
     should reset when the loop is reset.

4. Public intermediate observability:
   - Drive `trim_mon` as the bounded calibration control/trim voltage.
   - Drive `residual_mon` as the post-correction residual-error monitor around
     the 0.45 V center point.
   - Positive raw error should move `trim_mon` below center; negative raw error
     should move it above center, and `residual_mon` should be closer to center
     than the raw error stimulus after the loop update.

The expected public relation is: `vin` error excursion -> bounded corrective
`trim_mon` response -> reduced `residual_mon` -> bounded corrective `out`
response -> `metric` tracking convergence of the calibration loop.

## Output Contract

Return exactly these source artifacts:

- `complete_calibration_loop.va`
- `tb_complete_calibration_loop.scs`

Do not include explanatory prose outside the source artifact contents.

## Task-Specific Public Description

### Complete calibration loop (end-to-end)

Write both the Verilog-A behavioral module and a Spectre transient testbench.

Behavioral intent:

Close a simple calibration loop from error stimulus through controller and actuator output.

Module name: `complete_calibration_loop`.
Domain: pure voltage-domain behavioral Verilog-A.
Do not use current contributions, transistor-level devices, AC/noise analysis,
or KCL/KVL solving assumptions.

Public port contract:

```verilog
module complete_calibration_loop(clk, rst, vin, out, metric, trim_mon, residual_mon);
input clk, rst, vin;
output out, metric, trim_mon, residual_mon;
electrical clk, rst, vin, out, metric, trim_mon, residual_mon;
```

Signal contract:

clk and rst are voltage-coded logic signals, low=0 V and high=0.9 V with threshold 0.45 V. vin is the external offset/error stimulus around 0.45 V. The internal controller drives correction opposite the measured residual error, trim_mon is the public bounded trim/control voltage, residual_mon is the post-correction residual monitor around 0.45 V, out is the bounded corrected plant response, and metric is high when out is close to 0.45 V.

Saved waveform columns:

```text
clk rst vin out metric trim_mon residual_mon
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
