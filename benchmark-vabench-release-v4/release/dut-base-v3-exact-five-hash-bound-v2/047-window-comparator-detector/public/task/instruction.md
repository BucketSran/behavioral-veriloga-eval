# Window Comparator Detector

## Task Contract

Implement the requested Verilog-A artifact for `Window Comparator Detector`.
- Form: `dut`
- Level: `L1`
- Category: `comparator_decision`
- Target artifact(s): `window_comparator_ref.va`

Implement a voltage-domain window comparator detector.

## Public Verilog-A Interface

Declare module `window_comparator_ref` with positional ports `VDD, VSS, vin,
out`. All ports are electrical. `VDD` and `VSS` are supply rails, `vin` is the
input voltage, and `out` is the in-window decision output.

## Public Parameter Contract

Provide these overrideable public parameters:

- `vlow = 0.3 V`: lower window threshold.
- `vhigh = 0.6 V`: upper window threshold.
- `tedge = 200p`: output transition smoothing time.

## Required Behavior

- Initialize the decision from the initial input voltage.
- Drive `out` high only while `vlow < V(vin,VSS) < vhigh`.
- Drive `out` low when `V(vin,VSS) <= vlow` or `V(vin,VSS) >= vhigh`.
- Resolve crossings of both the lower and upper thresholds in both directions.
- Drive `out` rail-to-rail relative to `VDD` and `VSS` using finite
  transition-style smoothing.

## Modeling Constraints

Return only `window_comparator_ref.va`. Use voltage contributions only. Do not
modify or emit the support harness, add validation logic, hard-code waveform
sample points, add simulator-specific side channels, use transistor-level
devices, current contributions, `ddt()`, or `idt()`. Update retained in-window
state at threshold-crossing events and drive the output contribution outside
those event blocks.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. The public example harness is a public validation scenario; do not hard-code a particular stimulus table, runtime horizon, or sampling window into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `window_comparator_ref.va`. Do not include explanatory prose outside the source artifact contents.
