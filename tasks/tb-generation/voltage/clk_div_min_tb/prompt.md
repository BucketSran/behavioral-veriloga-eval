Given a voltage-domain clock divider DUT, generate a minimal Spectre-format
`.scs` testbench suitable for EVAS.

DUT module to instantiate: `clk_div_min`

DUT ports:
- `VDD`: inout electrical (power rail)
- `VSS`: inout electrical (power rail)
- `CLK`: input electrical
- `RST_N`: input electrical
- `CLK_OUT`: output electrical

Requirements:

- provide `VDD`, `VSS`, input clock, and reset stimulus
- instantiate the DUT by position
- include `tran`
- include explicit `save`
- place `ahdl_include` last

DUT module to instantiate: `clk_div_min`

DUT ports:
- `VDD`: inout electrical (power rail)
- `VSS`: inout electrical (power rail)
- `CLK`: input electrical
- `RST_N`: input electrical
- `CLK_OUT`: output electrical

DUT module to instantiate: `clk_div_min`

DUT ports:
- `VDD`: electrical
- `VSS`: electrical
- `CLK`: electrical
- `RST_N`: electrical
- `CLK_OUT`: electrical

DUT module to instantiate: `clk_div_min`

DUT ports:
- `VDD`: electrical
- `VSS`: electrical
- `CLK`: electrical
- `RST_N`: electrical
- `CLK_OUT`: electrical

DUT module to instantiate: `clk_div_min`

DUT ports:
- `VDD`: electrical
- `VSS`: electrical
- `CLK`: electrical
- `RST_N`: electrical
- `CLK_OUT`: electrical

DUT module to instantiate: `clk_div_min`

DUT ports:
- `VDD`: electrical
- `VSS`: electrical
- `CLK`: electrical
- `RST_N`: electrical
- `CLK_OUT`: electrical

DUT module to instantiate: `clk_div_min`

DUT ports:
- `VDD`: electrical
- `VSS`: electrical
- `CLK`: electrical
- `RST_N`: electrical
- `CLK_OUT`: electrical

DUT module to instantiate: `clk_div_min`

DUT ports:
- `VDD`: electrical
- `VSS`: electrical
- `CLK`: electrical
- `RST_N`: electrical
- `CLK_OUT`: electrical

DUT module to instantiate: `clk_div_min`

DUT ports:
- `VDD`: electrical
- `VSS`: electrical
- `CLK`: electrical
- `RST_N`: electrical
- `CLK_OUT`: electrical

DUT module to instantiate: `clk_div_min`

DUT ports:
- `VDD`: electrical
- `VSS`: electrical
- `CLK`: electrical
- `RST_N`: electrical
- `CLK_OUT`: electrical

DUT module to instantiate: `clk_div_min`

DUT ports:
- `VDD`: electrical
- `VSS`: electrical
- `CLK`: electrical
- `RST_N`: electrical
- `CLK_OUT`: electrical

DUT module to instantiate: `clk_div_min`

DUT ports:
- `VDD`: electrical
- `VSS`: electrical
- `CLK`: electrical
- `RST_N`: electrical
- `CLK_OUT`: electrical

DUT module to instantiate: `clk_div_min`

DUT ports:
- `VDD`: electrical
- `VSS`: electrical
- `CLK`: electrical
- `RST_N`: electrical
- `CLK_OUT`: electrical


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=24n maxstep=20p
```

Required public waveform columns in `tran.csv`:

- `CLK`, `RST_N`, `CLK_OUT`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Reset-like input(s) `reset`, `RST_N` must be asserted only for startup/explicit reset checks, then deasserted early enough and kept deasserted through the post-reset checking window.
- For active-low resets such as `rstb`, `rst_n`, or `rst_ni`, avoid a finite-width pulse that returns the reset node low after release; use a waveform that remains high during checking.
- Clock-like input(s) `clock`, `CLK` must provide enough valid edges after reset/enable for the checker to sample settled outputs.
- Sequential outputs are sampled shortly after clock edges, so drive outputs with stable held state variables and `transition()` targets rather than glitchy combinational expressions.
- Public stimulus nodes used by the reference harness include: `VDD`, `VSS`, `CLK`, `RST_N`.
