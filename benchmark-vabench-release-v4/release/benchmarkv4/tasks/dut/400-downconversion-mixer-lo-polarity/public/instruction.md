# Downconversion Mixer with LO Polarity

## Task Contract

Implement a Verilog-A DUT source package for a mixed-signal behavioral circuit block.

- Target artifacts: `downconversion_mixer_lo_polarity.va`
- Public top module: `downconversion_mixer_lo_polarity`
- Required public module: `downconversion_mixer_lo_polarity`

The submitted source must include the target artifact and public module listed above. The public top module is the module instantiated by the evaluator; optional helper modules may be included only when they are part of the DUT source package, not testbench code.

## Public Verilog-A Interface

Declare top module `downconversion_mixer_lo_polarity` with positional electrical ports `rf_in, lo_i, lo_q, rst, enable, i_out, q_out, lo_i_metric, lo_q_metric, polarity_ok`. All top-level ports are electrical.

The top module must expose exactly the public top-level port order above. Optional implementation-local helper modules are allowed, but no helper module is required by the public contract.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vcm = 0.45 V`: common-mode reference for single-ended signals.
- `vth = 0.45 V`: threshold for LO and control inputs.
- `conversion_gain = 0.5`: baseband conversion gain from RF deviation.
- `tr = 200 ps`: smoothing time for discrete LO-polarity and status transitions; continuous RF-dependent output values remain continuous analog contributions.

## Required Behavior

- On reset or when `enable` is low, drive `i_out` and `q_out` to `vcm`, clear LO metrics, and clear `polarity_ok`.
- Interpret `lo_i` and `lo_q` as voltage-coded quadrature LO polarity controls.
- Map each LO control to signed multiplier `s`: high means `s = +1` and low
  means `s = -1`.
- Drive `i_out = vcm + conversion_gain * (V(rf_in) - vcm) * s_i` and
  `q_out = vcm + conversion_gain * (V(rf_in) - vcm) * s_q` before clamping.
- Clamp `i_out` and `q_out` to `[vss, vdd]`.
- `lo_i_metric` and `lo_q_metric` must be `vdd` for positive polarity and
  `vss` for negative polarity.
- Assert `polarity_ok` only after both LO controls have been observed toggling while enabled.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add testbench code, Spectre decks, checker code, generated result files, debug-only ports, or pass/fail flags.

This is a DUT circuit-block task: implement the observable behavior directly and keep any optional internal decomposition solver-owned. The evaluator may use behavior checks to validate the top-level observable contract.

## Output Contract

Return exactly these complete source artifacts:

- `downconversion_mixer_lo_polarity.va`
