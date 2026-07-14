# Precision Rectifier Envelope Detector

## Task Contract

Implement the requested Verilog-A artifact for `Precision Rectifier Envelope Detector`.
- Form: `dut`
- Level: `L1`
- Category: `baseband_signal_conditioning`
- Target artifact(s): `precision_rectifier_envelope_detector.va`

Implement `precision_rectifier_envelope_detector.va` in Verilog-A.

Declare module
`precision_rectifier_envelope_detector(clk, rst, vin, rect, env, metric)` with
all ports electrical. `clk` and `rst` are voltage-coded logic signals with a
0.45 V threshold. `vin` is an analog input around `vcm`, `rect` is the
full-wave rectified magnitude around common mode, `env` is a peak-envelope
state, and `metric` marks envelope hold memory.

Public parameters:

- `vth`: logic threshold, default `0.45`.
- `vcm`: rectifier common mode, default `0.45`.
- `decay`: envelope decay step per clock update, default `0.018`.
- `tr`: output transition time, default `150p`.

Behavior:

- Rectify the absolute deviation around common mode: zero input deviation maps
  `rect` to `vcm`, and either polarity of input excursion increases `rect`.
- Clip `rect` to the available 0 V to 0.9 V voltage range.
- Update `env` on rising `clk` crossings.
- When `rst` is high, return `env` to `vcm` and clear envelope memory.
- When the rectified input exceeds the stored envelope, update the envelope
  quickly to the new peak.
- When the rectified input falls below the stored envelope, let the envelope
  decay gradually while staying at or above the instantaneous rectified value
  and not falling below `vcm`.
- Drive `metric` high when `env - rect` is greater than `30 mV`; otherwise drive `metric` low.

Modeling requirements:

- Use voltage contributions only; do not use current contributions,
  transistor-level devices, AC/noise analysis, or KCL/KVL assumptions.
- `rect` is a continuous rectified voltage expression and should be driven as a
  direct voltage contribution. `env` and `metric` are clocked states and should
  be driven through `transition(...)`.
- Return only `precision_rectifier_envelope_detector.va`; do not emit a Spectre
  testbench or validation harness.

## Public Verilog-A Interface

Declare module `precision_rectifier_envelope_detector` with positional ports `clk, rst, vin, rect, env, metric`. All ports are electrical. `clk` and `rst` are voltage-coded control inputs, `vin` is the analog signal around the common-mode level, `rect` is the instantaneous rectified output, `env` is the sampled envelope state, and `metric` reports envelope lag.

## Public Parameter Contract

Provide these overrideable public parameters:

- `vth = 0.45 V`: logic threshold for `clk` and `rst`.
- `vcm = 0.45 V`: common-mode level for rectification and envelope reset.
- `decay = 0.018 V/update`: envelope decay amount per sampled update.
- `tr = 150 ps`: transition smoothing time for `env` and `metric`.

## Required Behavior

- Compute `rect` as a precision full-wave rectified voltage around `vcm`, bounded to the valid signal range.
- Initialize the envelope state to `vcm`.
- On each rising `clk` crossing, reset the envelope state to `vcm` when `rst` is above `vth`.
- When not reset, update the envelope by immediately following upward rectified peaks and otherwise decaying by `decay` toward the current rectified level.
- Do not let the envelope decay below either the current rectified level or `vcm`.
- Drive `metric` high when the envelope exceeds the instantaneous rectified value by more than `30 mV`, and low otherwise.

## Modeling Constraints

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `precision_rectifier_envelope_detector.va`. Do not include explanatory prose outside the source artifact contents.
