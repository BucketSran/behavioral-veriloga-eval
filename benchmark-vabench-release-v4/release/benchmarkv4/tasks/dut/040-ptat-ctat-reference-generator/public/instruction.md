# PTAT/CTAT Reference Generator

## Task Contract

Implement the requested Verilog-A artifact for `PTAT CTAT Reference Generator`.
- Form: `dut`
- Level: `L1`
- Category: `bias_reference_power_management`
- Target artifact(s): `ptat_ctat_reference_generator.va`

Implement a clocked voltage-domain PTAT/CTAT reference macro model. Return only the requested DUT artifact; do not generate a testbench.

## Public Verilog-A Interface

```verilog
module ptat_ctat_reference_generator(clk, rst, vin, out, metric);
input clk, rst, vin;
output out, metric;
electrical clk, rst, vin, out, metric;
```

## Public Parameter Contract

Provide these overrideable public parameters:

- `tr = 100 ps`: output transition rise/fall smoothing time.
- `vth = 0.45 V`: voltage-coded logic threshold for `clk` and `rst`.

## Required Behavior

- `clk` and `rst` are voltage-coded logic signals.
- Treat `vin` as a normalized temperature/control voltage in the 0 V to 0.9 V range.
- Reset should initialize `out` to 0.45 V and drive `metric` to 0 V until
  valid updates occur.
- On each rising `clk` crossing with reset low, clamp the sampled temperature
  input to `[0 V, 0.9 V]`.
- Compute the PTAT branch as `0.18 V + 0.34 * vin_clamped` and the CTAT branch
  as `0.78 V - 0.34 * vin_clamped`.
- Drive the reference output as the equal-weight branch average:
  `out = 0.5 * ptat + 0.5 * ctat`.
- Drive `metric` as the PTAT branch voltage so it increases with the
  temperature/control input.
- Clamp the driven `out` voltage to the public 0 V to 0.9 V voltage-domain
  range.
- Keep the model pure voltage-domain behavioral Verilog-A. Do not use branch-current contributions, transistor-level devices, AC/noise analysis, or KCL/KVL regulation loops.

## Modeling Constraints

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one source artifact named `ptat_ctat_reference_generator.va`.
Do not include explanatory prose outside the source artifact contents.
