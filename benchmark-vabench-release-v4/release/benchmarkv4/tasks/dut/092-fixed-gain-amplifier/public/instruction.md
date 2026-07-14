# Fixed Gain Amplifier

## Task Contract

Implement the requested Verilog-A artifact for `Fixed Gain Amplifier`.
- Form: `dut`
- Level: `L1`
- Category: `measurement_instrumentation_flows`
- Target artifact(s): `gain_amp_fixed.va`

Implement `gain_amp_fixed.va` in Verilog-A.

## Public Verilog-A Interface

```verilog
module gain_amp_fixed(
    input  electrical VIN_P,
    input  electrical VIN_N,
    output electrical VOUT_P,
    output electrical VOUT_N
);
```

## Public Parameter Contract

The public parameters declared by the target artifact are part of the contract and may be overridden by validation harnesses. Preserve their names, defaults, ranges, and meanings:

- `parameter real vdd = 0.9;` in `gain_amp_fixed.va`.
- `parameter real ACTUAL_GAIN = 8.64;` in `gain_amp_fixed.va`.

## Required Behavior

Implement a standalone fixed-gain differential amplifier. The module receives
`VIN_P/VIN_N`, computes the input differential voltage, multiplies it by the
`ACTUAL_GAIN` parameter, and produces a differential output centered around
`vdd/2`:

```text
vout_diff = ACTUAL_GAIN * (VIN_P - VIN_N)
VOUT_P = vdd/2 + vout_diff / 2
VOUT_N = vdd/2 - vout_diff / 2
```

The amplifier must preserve output common-mode at `vdd/2`, keep positive
polarity from input differential to output differential, and honor different
`ACTUAL_GAIN` and `vdd` values supplied by the testbench.

Public parameters:

- `ACTUAL_GAIN = 8.64`: positive dimensionless differential voltage gain.
- `vdd = 0.9 V`: positive output common-mode supply parameter; the nominal
  output common-mode is `vdd/2`.

Honor legal testbench overrides of both parameters while preserving positive
differential polarity and common-mode behavior.

Keep the model pure behavioral Verilog-A. Do not use transistor-level devices,
AC/noise analysis, waveform files, validation artifacts, or simulator side
channels.

Only `gain_amp_fixed.va` is graded as the candidate implementation.

## Modeling Constraints

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `gain_amp_fixed.va`. Do not include explanatory prose outside the source artifact contents.
