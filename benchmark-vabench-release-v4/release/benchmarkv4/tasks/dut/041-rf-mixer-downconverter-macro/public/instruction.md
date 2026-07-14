# RF Mixer Downconverter Macro

## Task Contract

Implement the requested Verilog-A artifact for `RF Mixer Downconverter Macro`.
- Form: `dut`
- Level: `L1`
- Category: `rf_afe_behavioral_macromodels`
- Target artifact(s): `rf_mixer_downconverter_macro.va`

Implement a voltage-domain RF mixer/downconverter macromodel.

## Public Verilog-A Interface

Declare module `rf_mixer_downconverter_macro` with positional ports `clk, rst,
vin, out, metric`. All ports are electrical.

`clk` is the LO-polarity waveform, `rst` is an active-high voltage-coded reset,
`vin` is an RF input envelope centered around common mode, `out` is the
baseband output, and `metric` indicates active conversion.

## Public Parameter Contract

Provide these overrideable public parameters:

- `tr = 80p`: transition time used for smoothed voltage contributions.
- `vth = 0.45 V`: threshold for voltage-coded logic decisions.
- `conv_gain = 1.25`: conversion gain applied to the RF envelope deviation.

## Required Behavior

When reset is asserted, drive `out` to the 0.45 V common-mode level and drive
`metric` low. After reset releases, interpret `clk` as the LO polarity: use
LO coefficient `+1.0` when `clk > vth`, and `-1.0` otherwise. Compute the
converted baseband target as
`0.45 V + conv_gain * (vin - 0.45 V) * LO_coefficient`. Clamp the driven `out`
voltage to `[0.02 V, 0.88 V]`. Drive `metric` to 0.9 V while conversion is
active.

## Modeling Constraints

Return only `rf_mixer_downconverter_macro.va`. Use voltage contributions only.
Use behavioral state and `transition(...)` smoothing where the target output can
change discontinuously. Do not modify or emit the support harness, add validation
logic, hard-code specific waveform sample points, add simulator-specific side
channels, use current contributions, transistor-level devices, S-parameters,
AC/noise-analysis behavior, communication modem algorithms, or full link-level
decoding.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The public example harness is a public validation scenario; do not hard-code a particular stimulus table, runtime horizon, or sampling window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `rf_mixer_downconverter_macro.va`. Do not include explanatory prose outside the source artifact contents.
