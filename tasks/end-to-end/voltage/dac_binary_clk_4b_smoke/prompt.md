Write a Verilog-A module named `dac_binary_clk_4b`.

Create a voltage-domain 4-bit clocked binary DAC in Verilog-A,
then produce a minimal EVAS-compatible Spectre testbench and run a smoke simulation.

Behavioral intent:

- four 1-bit digital inputs `din3` (MSB), `din2`, `din1`, `din0` (LSB)
- one clock input `rdy` and one analog output `aout`
- on each rising edge of `rdy`, sample the 4-bit input code and update `aout`
- transfer function: `aout = (8*din3 + 4*din2 + 2*din1 + din0) / 16 * vref`
- output transitions smoothly using `transition(...)` with 100 ps rise/fall

Implementation constraints:

- pure voltage-domain Verilog-A only
- EVAS-compatible syntax
- use `@(cross(...))` for clock edge detection
- use `transition(...)` to drive `aout`
- `rdy`, `din3`, `din2`, `din1`, `din0`, and `aout` must appear in the waveform CSV

Minimum simulation goal:

- vref=0.9 V, sweep all 16 codes (0 to 15) in order, one code per 40 ns clock period,
  run for 660 ns
- `aout` must produce at least 14 distinct output levels
- output must be monotonically non-decreasing as the input code increases
- full output range (code 0 to code 15) must span at least 75% of vref

Expected behavior:
- aout should be monotonic: increasing digital code → increasing analog output
- At least 14 different output levels should be produced
- Output span (max - min) should be ≥ 0.7V
- Each din bit represents a binary weight: din0=1, din1=2, din2=4, din3=8
Ports:
- `DIN3`: input electrical
- `DIN2`: input electrical
- `DIN1`: input electrical
- `DIN0`: input electrical
- `CLK`: input electrical
- `AOUT`: output electrical


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=660n maxstep=200p
```

Required public waveform columns in `tran.csv`:

- `din3`, `din2`, `din1`, `din0`, `aout`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Clock-like input(s) `clock`, `CLK` must provide enough valid edges after reset/enable for the checker to sample settled outputs.
- Sequential outputs are sampled shortly after clock edges, so drive outputs with stable held state variables and `transition()` targets rather than glitchy combinational expressions.
- Public stimulus nodes used by the reference harness include: `rdy`, `din3`, `din2`, `din1`, `din0`.
