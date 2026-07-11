# PFD UP/DN Reset-Race Logic

## Task Contract

Implement the requested Verilog-A artifact for `PFD Up DN Logic`.
- Form: `dut`
- Level: `L1`
- Category: `pll_clock_timing`
- Target artifact(s): `pfd_updn.va`

Implement `pfd_updn.va` in Verilog-A.

## Public Verilog-A Interface

```verilog
module pfd_updn (
    inout  electrical VDD,
    inout  electrical VSS,
    input  electrical REF,
    input  electrical DIV,
    output electrical UP,
    output electrical DN
);
```

## Public Parameter Contract

Provide these overrideable public parameters:

| Parameter | Default | Unit / Range | Contract |
| --- | ---: | --- | --- |
| `vth` | `0.45` | V | Rising-edge threshold for `REF` and `DIV`. |
| `tedge` | `20 ps` | time, `(0:inf)` | Rise/fall smoothing for `UP` and `DN`. |

## Required Behavior

The module is a voltage-domain phase-frequency detector UP/DN generator with reset-race clearing.

- Detect rising `REF` and `DIV` crossings at `vth`.
- Set `UP` high on a rising `REF` edge and keep it high until a qualifying
  reset-race clear.
- Set `DN` high on a rising `DIV` edge and keep it high until a qualifying
  reset-race clear.
- If a rising edge arrives while the opposite output state is already high,
  clear both `UP` and `DN` immediately. This must work when `REF` leads `DIV`
  and when `DIV` leads `REF`.
- Falling input edges must not set either output.
- After a reset-race clear, both outputs must remain low until the next rising
  input edge.
- Do not intentionally hold both `UP` and `DN` high beyond analog smoothing
  overlap.
- Drive `UP` and `DN` as smoothed voltage-domain logic levels referenced to
  `VDD` for high and `VSS` for low.

## Modeling Constraints

Use voltage contributions only. Do not use current contributions, `ddt()`,
`idt()`, transistor-level devices, AC/noise analysis, validation logic, validation-only
test hooks, or simulator-specific side channels.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The visible testbench is a public validation scenario; do not hard-code a particular stimulus table, transient stop time, or validation sample window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one source artifact named `pfd_updn.va`.
