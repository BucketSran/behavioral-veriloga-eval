# Bipolar DAC 4b Continuous

## Task Contract

Implement the requested Verilog-A artifact for `Bipolar DAC 4b Continuous`.
- Form: `dut`
- Level: `L1`
- Category: `data_converter`
- Target artifact(s): `bipolar_dac_4b_continuous.va`

Implement the Verilog-A DUT `bipolar_dac_4b_continuous` in `bipolar_dac_4b_continuous.va`.

## Public Verilog-A Interface

The module port order is:

```text
vd3, vd2, vd1, vd0, vout
```

All ports are electrical. `vd3` is the MSB and `vd0` is the LSB.

## Public Parameter Contract

- `vref = 0.9`: bipolar output full-scale magnitude in volts.
- `vtrans = 0.45`: input logic threshold in volts.
- `tdel = 0`, `trise = 20p`, `tfall = 20p`: transition timing for `vout`.

## Required Behavior

Continuously decode the four input voltages into an unsigned binary code. An input bit is logic 1 when its voltage is greater than `vtrans`, otherwise it is logic 0.

Drive `vout` as a linear bipolar DAC output. Code 0 must produce approximately `-vref`, code 15 must produce approximately `+vref`, and each one-code increase must raise the output by the same voltage step. The output must be monotonic with the unsigned code.

## Modeling Constraints

Use voltage-domain Verilog-A behavior only. Do not use current contributions, `ddt()`, `idt()`, file I/O, or simulator-specific side channels.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The visible testbench is a public validation scenario; do not hard-code a particular stimulus table, transient stop time, or validation sample window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one source artifact named `bipolar_dac_4b_continuous.va`. Do not include explanatory prose outside the source artifact contents.
