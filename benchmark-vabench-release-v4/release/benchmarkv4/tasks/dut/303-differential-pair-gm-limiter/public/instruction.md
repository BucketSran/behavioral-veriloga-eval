# Differential-pair gm Limiter

## Task Contract

Implement a Verilog-A DUT source package for a mixed-signal behavioral circuit block.

- Target artifacts: `differential_pair_gm_limiter.va`
- Public top module: `differential_pair_gm_limiter`
- Required public module: `differential_pair_gm_limiter`

The submitted source must include the target artifact and public module listed above. The public top module is the top-level DUT entry point; optional helper modules may be included only when they are part of the returned DUT source package, not verification harness code.

## Public Verilog-A Interface

Declare top module `differential_pair_gm_limiter` with positional electrical ports `vinp, vinn, bias, enable, voutp, voutn, gm_metric, limit_flag`. All top-level ports are electrical.

The top module must expose exactly the public top-level port order above. Optional implementation-local helper modules are allowed, but no helper module is required by the public contract.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high and upper output rail.
- `vss = 0.0 V`: logic low and lower output rail.
- `vcm = 0.45 V`: signal common-mode reference.
- `vth = 0.45 V`: threshold for voltage-coded control inputs.
- `tr = 200 ps`: output transition smoothing time.
- `gm_gain = 4.0`: small-signal differential gain.
- `diff_limit = 120e-3 V`: differential input where limiting begins.

## Required Behavior

- When disabled, drive both outputs to `vcm`, clear `gm_metric`, and clear `limit_flag`.
- When enabled, convert the sampled differential input into equal-and-opposite output deviations around `vcm`.
- Scale small-signal output separation by `gm_gain` and compress large differential inputs smoothly at `diff_limit`.
- Drive `gm_metric` as a voltage-coded estimate of the active transconductance region.
- Assert `limit_flag` only when compression is active.
- Use only voltage-domain behavioral state and voltage contributions on public electrical outputs.
- Do not expose pass/fail flags; expose only the public observable metrics named in the interface.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add verification harnesses, simulation decks, generated result files, logs, reports, debug-only ports, or pass/fail flags.

This is a DUT circuit-block task: implement the observable behavior directly and keep any optional internal decomposition solver-owned. Keep the top-level observable behavior sufficient to validate the public contract under varied stimulus conditions.

## Output Contract

Return exactly these complete source artifacts:

- `differential_pair_gm_limiter.va`
