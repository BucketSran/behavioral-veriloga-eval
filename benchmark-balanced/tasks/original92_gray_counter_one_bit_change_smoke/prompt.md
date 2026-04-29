Write a pure voltage-domain Verilog-A 4-bit Gray-code counter.

Module name: `gray_counter_one_bit_change_ref`.

Requirements:

1. Ports: `vdd`, `vss`, `clk`, `rst`, `g0`, `g1`, `g2`, `g3`
2. On each rising edge of `clk`, if `rst` is low, increment a 4-bit binary count.
3. Drive outputs as Gray code: `gray = bin ^ (bin >> 1)`.
4. When `rst` is high, reset the counter to zero.
5. Adjacent output states must differ by exactly one bit.
6. Use only voltage-domain constructs compatible with EVAS.

Expected behavior:
- Between any two consecutive states, exactly one bit flips
- This is the defining property of Gray code
Ports:
- `vdd`: electrical
- `vss`: electrical
- `clk`: electrical
- `rst`: electrical
- `g0`: electrical
- `g1`: electrical
- `g2`: electrical
- `g3`: electrical (power rail)
- `vss`: inout electrical (power rail)
- `clk`: input electrical
- `rst`: input electrical
- `g0`: output electrical
- `g1`: output electrical
- `g2`: output electrical
- `g3`: output electrical

Write EVAS-compatible Verilog-A (pure voltage-domain behavioral model, no current contributions).

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
tran tran stop=220n maxstep=100p errpreset=conservative
```

Required public waveform columns in `tran.csv`:

- `clk`, `rst`, `g0`, `g1`, `g2`, `g3`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Reset-like input(s) `rst`, `reset` must be asserted only for startup/explicit reset checks, then deasserted early enough and kept deasserted through the post-reset checking window.
- For active-low reset inputs, avoid a finite-width pulse that returns the reset node low after release; use a waveform that remains high during checking.
- Clock-like input(s) `clk` must provide enough valid edges after reset/enable for the checker to sample settled outputs.
- Sequential outputs are sampled shortly after clock edges, so drive outputs with stable held state variables and `transition()` targets rather than glitchy combinational expressions.
- Public stimulus nodes used by the reference harness include: `vdd`, `vss`, `clk`, `rst`.
