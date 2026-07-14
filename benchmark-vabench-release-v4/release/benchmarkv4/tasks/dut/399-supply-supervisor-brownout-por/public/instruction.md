# Supply Supervisor with Brownout POR

## Task Contract

Implement a Verilog-A DUT source package for a mixed-signal behavioral circuit block.

- Target artifacts: `supply_supervisor_brownout_por.va`
- Public top module: `supply_supervisor_brownout_por`
- Required public module: `supply_supervisor_brownout_por`

The submitted source must include the target artifact and public module listed above. The public top module is the module instantiated by the evaluator; optional helper modules may be included only when they are part of the DUT source package, not testbench code.

## Public Verilog-A Interface

Declare top module `supply_supervisor_brownout_por` with positional electrical ports `vdd_sense, clk, rst, enable, por_n, pgood, brownout, delay_metric, state_metric`. All top-level ports are electrical.

The top module must expose exactly the public top-level port order above. Optional implementation-local helper modules are allowed, but no helper module is required by the public contract.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `voh = 0.9 V`: logic high output level.
- `vol = 0.0 V`: logic low output level.
- `vth = 0.45 V`: threshold for clock and control inputs.
- `uvlo_rise = 0.72 V`: supply rising threshold for leaving brownout.
- `uvlo_fall = 0.64 V`: supply falling threshold for entering brownout.
- `release_cycles = 4`: consecutive good clock cycles required before releasing reset.
- `tr = 100 ps`: output transition smoothing time.

## Required Behavior

- On reset or when `enable` is low, assert brownout, deassert `pgood`, drive `por_n` low, and clear delay/state metrics.
- Apply hysteresis to `vdd_sense`: enter brownout below `uvlo_fall` and leave brownout only after `vdd_sense` rises above `uvlo_rise`.
- After leaving brownout, count consecutive rising `clk` edges while the supply remains above `uvlo_rise`.
- Release `por_n` and assert `pgood` only after `release_cycles` consecutive good enabled cycles.
- If `vdd_sense` drops below `uvlo_fall`, immediately assert brownout, clear the release counter, deassert `pgood`, and drive `por_n` low.
- `delay_metric` must expose release count `k` as
  `vol + (voh - vol) * k / release_cycles`, saturated at `voh`.
- `state_metric` must map reset, brownout, counting, and released to
  `vol`, `vol + (voh - vol)/3`, `vol + 2*(voh - vol)/3`, and `voh`,
  respectively.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add testbench code, Spectre decks, checker code, generated result files, debug-only ports, or pass/fail flags.

This is a DUT circuit-block task: implement the observable behavior directly and keep any optional internal decomposition solver-owned. The evaluator may use behavior checks to validate the top-level observable contract.

## Output Contract

Return exactly these complete source artifacts:

- `supply_supervisor_brownout_por.va`
