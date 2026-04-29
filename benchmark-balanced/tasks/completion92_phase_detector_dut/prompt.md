Create only the DUT Verilog-A model for the core function below.
Do not generate a testbench; the evaluator will use a fixed public harness.

Core function family: phase-detector.
Balanced task-form completion derived from original task: `bbpd_data_edge_alignment_smoke`.

Spectre/Verilog-A compatibility requirements:
- Use voltage-domain electrical ports where applicable.
- Keep the public interface and saved observable behavior compatible with the evaluation harness.
- Prefer explicit `transition(...)` on driven voltage outputs.
- Avoid current contributions, `ddt()`, `idt()`, simulator control blocks, and non-Spectre syntax.

Source behavioral specification:

Write a voltage-domain Alexander-style bang-bang phase detector (BBPD) that captures
near-edge data/clock alignment behavior.

Module name: `bbpd_data_edge_alignment_ref`.

Requirements:

1. Ports: `vdd`, `vss`, `clk`, `data`, `up`, `dn`, `retimed_data`
2. Use event-driven edge handling with EVAS-compatible `cross()`
3. Emit bounded UP/DN pulses according to data-edge alignment around the clock
4. Keep UP and DN mostly non-overlapping
5.  Stay in pure electrical voltage domain

Expected behavior:
- up pulse should fire when data edge leads clock edge
- dn pulse should fire when data edge lags clock edge
- up and dn should NOT overlap (overlap_frac < 2%)
- At least 6 data edges should generate up/dn pulses
Ports:
- `vdd`: electrical
- `vss`: electrical
- `clk`: electrical
- `data`: electrical
- `up`: electrical
- `dn`: electrical
- `retimed_data`: electrical (power rail)
- `vss`: inout electrical (power rail)
- `clk`: input electrical
- `data`: input electrical
- `up`: output electrical
- `dn`: output electrical
- `retimed_data`: output electrical

Implement this in Verilog-A behavioral modeling.

## Output Contract (MANDATORY)

- Return exactly two fenced code blocks:
  - first block: Verilog-A DUT (` ```verilog-a ... ``` `)
  - second block: Spectre testbench (` ```spectre ... ``` `)
- The Spectre testbench must include the DUT with `ahdl_include "<module>.va"`.
- Use a single `tran` analysis and include the required `save` signals for checker evaluation.


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=170n maxstep=0.1n
```

Required public waveform columns in `tran.csv`:

- `clk`, `data`, `up`, `dn`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Clock-like input(s) `clk`, `clock` must provide enough valid edges after reset/enable for the checker to sample settled outputs.
- Sequential outputs are sampled shortly after clock edges, so drive outputs with stable held state variables and `transition()` targets rather than glitchy combinational expressions.
- Public stimulus nodes used by the reference harness include: `vdd`, `vss`, `clk`, `data`.
