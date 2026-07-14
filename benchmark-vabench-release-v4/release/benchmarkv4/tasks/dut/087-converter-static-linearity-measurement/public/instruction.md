# Converter Static Linearity Measurement

## Task Contract

Implement the requested Verilog-A artifact for `Converter Static Linearity Measurement`.
- Form: `dut`
- Level: `L2`
- Category: `data_converter_models`
- Target artifact(s): `converter_static_linearity_measurement_flow.va`

Implement one Verilog-A source file named
`converter_static_linearity_measurement_flow.va`.

## Public Verilog-A Interface

```verilog
module converter_static_linearity_measurement_flow(clk, rst, vin, code, recon, dnl, inl);
```

All ports are electrical. `clk` is the sampling strobe, `rst` is an
active-high reset, `vin` is the swept converter input, and `code`, `recon`,
`dnl`, and `inl` are analog metric outputs.

## Public Parameter Contract

- `vth = 0.45 V`: threshold for voltage-coded clock and reset logic.
- `vfs = 0.9 V`: full-scale input range for the 4-bit converter sweep.
- `tr = 120p`: transition smoothing time for the metric outputs.

## Required Behavior

This is an L2 converter measurement-flow component, not just an ideal quantizer.
On each rising crossing of `clk`, reset the retained state when `rst` is high.
Otherwise, clip `vin` to the 0-to-`vfs` range, quantize it to a 4-bit code, and
drive `code` as the code index times `vfs / 15`.

Drive `recon` from this public monotonic non-ideal reconstruction table for
codes 0 through 15. The numbers below are the default voltages for
`vfs = 0.9 V`; for any legal `vfs` override, scale each table entry by
`vfs / 0.9`.

```text
0.000, 0.055, 0.118, 0.182, 0.245, 0.303, 0.366, 0.428,
0.491, 0.553, 0.612, 0.674, 0.735, 0.798, 0.855, 0.900
```

Use the ideal 4-bit reference ramp `ideal_recon = (vfs / 15) * code_index`.
Drive `inl` as:

```text
inl = clamp(0.45 + 3.0 * (recon - ideal_recon), 0.05, 0.85)
```

For `dnl`, retain the previous valid code and reconstruction. When the current
code is greater than the previous code, compute:

```text
ideal_step = (vfs / 15) * (code_index - previous_code_index)
step_err = (recon - previous_recon) - ideal_step
dnl = clamp(0.45 + 4.0 * step_err, 0.05, 0.85)
```

When there is no previous valid increasing code step, drive `dnl = 0.45`.

**Public Verification Context**

The public transient scenario saves `clk`, `rst`, `vin`, `code`, `recon`, `dnl`,
and `inl` over a converter sweep. Treat those values as the verification
scenario for observable behavior, not as DUT implementation details.

## Modeling Constraints

Use voltage-domain event-driven Verilog-A only. Do not emit a Spectre
testbench, validation logic, specific waveform sample points, current
contributions, transistor-level devices, AC/noise analysis, `ddt()`, or
`idt()`.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `converter_static_linearity_measurement_flow.va`. Do not include explanatory prose outside the source artifact contents.
