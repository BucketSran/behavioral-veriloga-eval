# Deadband Diffamp

## Task Contract
Implement `deadband_diffamp.va`, a differential deadband amplifier with asymmetric gain and leakage output. This is a baseband L1 DUT distinct from a single-ended deadband shaper because it uses differential input polarity and independent low/high gain branches.

## Public Verilog-A Interface
Declare module `deadband_diffamp(sigin_p, sigin_n, sigout)` with scalar electrical ports. `sigin_p` and `sigin_n` form the differential input; `sigout` is the output voltage.

## Public Parameter Contract
Provide overrideable public parameters:

- `sigin_dead_low = -0.1 V`: inclusive lower differential deadband edge.
- `sigin_dead_high = 0.1 V`: inclusive upper differential deadband edge.
- `sigout_leak = 0.02 V`: output level inside the deadband.
- `gain_low = 2.0`: low-side gain.
- `gain_high = 3.0`: high-side gain.

## Required Behavior
Compute the differential input from `sigin_p` to `sigin_n`. Inside the deadband, including both thresholds, drive `sigout_leak`. Below the lower threshold, drive the low-side signed residue using `gain_low` and add the leakage level. Above the upper threshold, drive the high-side signed residue using `gain_high` and add the leakage level.

## Modeling Constraints
Use deterministic voltage-domain Verilog-A and voltage contributions only. Do not emit a testbench, checker logic, out-of-band test hooks, hard-code testbench sample points, use current contributions, transistor-level devices, `ddt()`, `idt()`, or simulator side channels.

## Output Contract
Return exactly one source artifact named `deadband_diffamp.va`.
