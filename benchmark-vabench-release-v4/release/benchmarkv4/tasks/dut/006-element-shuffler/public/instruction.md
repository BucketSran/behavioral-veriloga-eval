# Element Shuffler

## Task Contract

Implement the requested Verilog-A artifact for `Element Shuffler`.
- Form: `dut`
- Level: `L1`
- Category: `calibration_control`
- Target artifact(s): `element_shuffler.va`

Implement a deterministic voltage-domain one-hot element shuffler for calibration or dynamic-element-matching control. Return only the requested DUT artifact; do not generate a testbench.

## Public Verilog-A Interface

The file `element_shuffler.va` must define module `element_shuffler` with positional ports:

```verilog
module element_shuffler(clk, rst_n, out0, out1, out2, out3);
```

All ports are electrical. `clk` and `rst_n` are voltage-coded control inputs; `out0` through `out3` are one-hot voltage-coded outputs.

## Public Parameter Contract

Provide these overrideable public parameters:

- `vth = 0.45 V`: logic threshold for `clk` and `rst_n`.
- `vdd = 0.9 V`: logic high level for the active output.
- `tr = 300 ps`: transition smoothing time for output changes.

## Required Behavior

Treat `clk` and `rst_n` as voltage-coded logic signals using threshold `vth`.

`rst_n` is active low. When `rst_n` is low, the shuffler must reset its internal state so the first valid rising edge of `clk` after reset release produces `out2` as the active output.

After reset is released, the active output must advance on each rising edge of `clk` through this repeating permutation:

```text
out2 -> out0 -> out3 -> out1 -> out2 -> ...
```

Exactly one of `out0`, `out1`, `out2`, and `out3` must be high in each stable state. Active outputs should be near `vdd`; inactive outputs should be near `0 V`.

The output sequence must be driven by `clk` and `rst_n` behavior, not by absolute simulation time.

## Modeling Constraints

Use voltage contributions only.

Do not use current contributions, transistor-level devices, `ddt()`, `idt()`, AC/noise analysis, validation-only hooks, or simulator-specific side channels.

Smooth output transitions with `transition(...)` or equivalent Verilog-A voltage contribution.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete Verilog-A file named `element_shuffler.va`.
Do not include explanatory prose outside the source artifact contents.
