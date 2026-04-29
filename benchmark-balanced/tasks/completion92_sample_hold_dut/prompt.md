Create only the DUT Verilog-A model for the core function below.
Do not generate a testbench; the evaluator will use a fixed public harness.

Core function family: sample-hold.
Balanced task-form completion derived from original task: `sample_hold_droop_smoke`.

Spectre/Verilog-A compatibility requirements:
- Use voltage-domain electrical ports where applicable.
- Keep the public interface and saved observable behavior compatible with the evaluation harness.
- Prefer explicit `transition(...)` on driven voltage outputs.
- Avoid current contributions, `ddt()`, `idt()`, simulator control blocks, and non-Spectre syntax.

Source behavioral specification:

Write a Verilog-A module named `sample_hold_droop_ref` and one minimal EVAS-compatible Spectre testbench.

# Task: sample_hold_droop_smoke

## Objective

Create a pure voltage-domain sample-and-hold model with observable hold droop. The testbench must
produce several sampling and hold windows so EVAS can measure droop behavior.

## DUT Contract

- Module name: `sample_hold_droop_ref`
- Ports, all `electrical`, exactly in this order: `vdd`, `vss`, `clk`, `vin`, `vout`
- Parameters:
  - `vth` real, default `0.45`
  - `tau` real, default `120n`
  - `dt` real, default `0.5n`
  - `trf` real, default `40p`
- Behavior:
  - Sample `V(vin)` on each rising edge of `clk`.
  - Between rising edges, hold the sampled value while adding finite droop toward `V(vss)`.
  - Output should remain in the supply range.
  - Use `@(cross(V(clk) - vth, +1))` and `transition(...)`.

## Testbench Contract

- Use a 0.9 V supply and 0 V reference.
- Drive `clk` with enough rising edges inside the final validation window to create multiple hold intervals.
- Drive `vin` through several distinct levels so the held output changes between samples.
- Instantiate the DUT by positional ports.
- Save these exact scalar names: `vin`, `clk`, `vout`.
- Include the generated DUT file `sample_hold_droop_ref.va`.
- Use the final transient setting listed in the Public Evaluation Contract below.

## Deliverables

Return exactly two fenced code blocks:

1. `sample_hold_droop_ref.va`
2. `tb_sample_hold_droop.scs`


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=170n maxstep=0.1n
```

Required public waveform columns in `tran.csv`:

- `vin`, `clk`, `vout`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Clock-like input(s) `clk` must provide enough valid edges after reset/enable for the checker to sample settled outputs.
- Sequential outputs are sampled shortly after clock edges, so drive outputs with stable held state variables and `transition()` targets rather than glitchy combinational expressions.
- Public stimulus nodes used by the reference harness include: `vdd`, `vss`, `clk`, `vin`.
