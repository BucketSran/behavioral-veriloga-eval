# Acquisition Limited Sample And Hold

## Task Contract

Implement the requested Verilog-A artifact for `Acquisition Limited Sample And Hold`.
- Form: `dut`
- Level: `L1`
- Category: `sampling_analog_memory`
- Target artifact(s): `acquisition_limited_sample_hold.va`

Implement `acquisition_limited_sample_hold.va` in Verilog-A.

## Public Verilog-A Interface

Declare module `acquisition_limited_sample_hold(sample, rst, vin, vout, metric)`
with scalar electrical voltage-domain ports.

- `sample`: voltage-coded acquisition-window control.
- `rst`: active-high voltage-coded reset.
- `vin`: analog input voltage.
- `vout`: acquired and held output voltage.
- `metric`: voltage-coded monitor that is high while the model is actively
  acquiring and low while it is holding or reset.

## Public Parameter Contract

- `vth`: logic threshold, default `0.45`.
- `vinit`: reset and initial held voltage, default `0.45`.
- `alpha`: acquisition fraction per update, default `0.42`.
- `tick`: acquisition update interval, default `1n`.
- `tr`: output and monitor transition smoothing time, default `200p`.

## Required Behavior

Model finite acquisition bandwidth rather than an ideal instantaneous sampler:

- A high `sample` level opens a tracking/acquisition window.
- While acquiring, `vout` moves toward the current `vin` voltage in discrete
  updates separated by `tick`.
- A falling `sample` crossing freezes the last acquired value.
- High `rst` returns the held output to `vinit` and clears the acquisition
  monitor.
- `metric` is high only while acquisition is active.

## Modeling Constraints

Return only `acquisition_limited_sample_hold.va`. Do not emit a the simulator
example harness, validation logic, validation-only hooks, or simulator-specific side
channels. Use voltage contributions only; do not use current contributions,
`ddt()`, or `idt()`.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The public example harness is a public validation scenario; do not hard-code a particular stimulus table, runtime horizon, or sampling window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `acquisition_limited_sample_hold.va`. Do not include explanatory prose outside the source artifact contents.
