# LFSR PRBS Generator

## Task Contract

Implement the requested Verilog-A artifact for `LFSR PRBS Generator`.
- Form: `dut`
- Level: `L1`
- Category: `stimulus_source_generators`
- Target artifact(s): `prbs7_ref.va`

Implement `prbs7_ref.va` in Verilog-A.

## Public Verilog-A Interface

Declare module `prbs7_ref` with positional ports:

```verilog
clk, rst_n, en, serial_out, state_0, state_1, state_2, state_3, state_4, state_5, state_6
```

All ports are electrical.

## Public Parameter Contract

- `vdd = 0.9 V`: high logic output level.
- `vth = 0.45 V`: clock, reset, and enable threshold.
- `trf = 10 ps`: output transition rise/fall time.
- `td = 0 ps`: output transition delay.
- `seed = 127`: reset seed. Legal public overrides are integers from `0` through `127` inclusive. If an override provides seed `0`, load `7'b0000001` instead of the all-zero lock-up state.

## Required Behavior

Create a clocked PRBS-7 stimulus source using a 7-bit LFSR with polynomial
`x^7 + x^6 + 1`. Treat `state_0` as bit 0 and `state_6` as bit 6. On reset,
load the public seed. On each rising crossing of `clk` through `vth`, advance
the LFSR only when `rst_n` and `en` are high. The feedback bit is:

```text
feedback = state_6 xor state_5
next_state_0 = feedback
next_state_i = previous_state_(i-1), for i = 1..6
```

Drive `serial_out` from `state_6` and expose each state bit on its matching
`state_i` output using voltage-coded `0`/`vdd` levels.

## Modeling Constraints

Return only `prbs7_ref.va`. Do not generate the validation harness or validation harness
logic. Do not use current contributions, `ddt()`, transistor-level devices,
AC/noise analysis, or simulator-specific side channels.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The public example harness is a public validation scenario; do not hard-code a particular stimulus table, runtime horizon, or sampling window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `prbs7_ref.va`. Do not include explanatory prose outside the source artifact contents.
