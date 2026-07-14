# TIA Limiting Receiver Macro

## Task Contract

Implement a Verilog-A DUT source package for a mixed-signal behavioral circuit block.

- Target artifacts: `tia_limiting_receiver.va`
- Public top module: `tia_limiting_receiver`
- Required public module: `tia_limiting_receiver`

The submitted source must include the target artifact and public module listed above. The public top module is the required deliverable boundary; optional helper modules may be included only when they are part of the DUT source package, not external stimulus or harness code.

## Public Verilog-A Interface

Declare top module `tia_limiting_receiver` with positional electrical ports `vin_proxy, clk, rst, enable, vout, decision, limit_flag, valid, amp_metric`. All top-level ports are electrical.

The top module must expose exactly the public top-level port order above. Optional implementation-local helper modules are allowed, but no helper module is required by the public contract.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vcm = 0.45 V`: receiver common-mode reference.
- `vth = 0.45 V`: threshold for clock and control inputs.
- `gain = 4.0`: voltage-domain input proxy gain.
- `limit = 0.35 V`: limiting excursion around `vcm`.
- `valid_min = 40e-3 V`: minimum amplitude metric required for valid.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset or when `enable` is low, drive `vout` to `vcm` and clear `decision`, `limit_flag`, `valid`, and `amp_metric`.
- Treat `vin_proxy` as a voltage-domain proxy for receiver input magnitude; no current ports are required.
- Apply gain to the deviation from `vcm` and clamp the output to `vcm +/- limit`.
- Assert `limit_flag` when the unclamped amplified signal would exceed the limiter range.
- On each rising `clk` edge, drive `decision` high when the limited output is at or above `vcm`, otherwise low.
- Assert `valid` when `amp_metric` is at least `valid_min` for two consecutive clock updates.
- `amp_metric` must expose the absolute limited signal deviation from `vcm`.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add external stimulus decks, private validation code, generated result files, debug-only ports, or pass/fail flags.

This is a DUT circuit-block task: implement the observable behavior directly and keep any optional internal decomposition solver-owned. The top-level observable contract should be verifiable from the public signals.

## Output Contract

Return exactly these complete source artifacts:

- `tia_limiting_receiver.va`
