Write a Verilog-A module named `serializer_8b`.

# Task: serializer_8b_smoke

## Objective

Create an 8-bit Parallel-to-Serial Converter behavioral model in Verilog-A and a minimal EVAS-compatible Spectre testbench.

## Specification

- **Module name**: `serializer_8b`
- **Ports** (all `electrical`, exactly as named): `vdd`, `vss`, `d7`, `d6`, `d5`, `d4`, `d3`, `d2`, `d1`, `d0`, `load`, `clk`, `sout`
- **Parameters**: `vth` (real, default 0.45), `tedge` (real, default 100p)
- **Behavior**:
  - Rising edge of `load`: latch `d7..d0` into internal 8-bit shift register, MSB first. Reset bit counter to 0. Drive `sout` with the MSB.
  - Rising edge of `clk` (when `load=0`): shift register left by 1; output next bit on `sout`.
  - After 8 CLK cycles, all bits serialized. Behavior undefined until next LOAD.
  - Output HIGH = V(vdd), LOW = V(vss) - read dynamically.
- **Output**: use `transition()` only.

## Testbench requirements

Create a minimal Spectre testbench that:
- Includes `serializer_8b.va` via `ahdl_include`
- Provides vdd=0.9V, vss=0V
- Sets parallel data input to distinct values
- Generates load and clock pulses
- Saves signals: `load`, `clk`, `d7`..`d0`, `sout`
- Runs transient for multiple serialization cycles

## Deliverable

Two files:
1. `serializer_8b.va` - the Verilog-A behavioral model
2. `tb_serializer_8b.scs` - the Spectre testbench

Expected behavior:
- 8-bit parallel input serialized to 1-bit output
- Frame alignment marker should indicate start of frame
Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `D7`: input electrical
- `D6`: input electrical
- `D5`: input electrical
- `D4`: input electrical
- `D3`: input electrical
- `D2`: input electrical
- `D1`: input electrical
- `D0`: input electrical
- `LOAD`: input electrical
- `CLK`: input electrical
- `SOUT`: output electrical


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=300n maxstep=1n
```

Required public waveform columns in `tran.csv`:

- `load`, `clk`, `sout`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Clock-like input(s) `clk`, `clock` must provide enough valid edges after reset/enable for the checker to sample settled outputs.
- Sequential outputs are sampled shortly after clock edges, so drive outputs with stable held state variables and `transition()` targets rather than glitchy combinational expressions.
- Public stimulus nodes used by the reference harness include: `vdd`, `vss`, `d7`, `d6`, `d5`, `d4`, `d3`, `d2`, `d1`, `d0`, `load`, `clk`.
