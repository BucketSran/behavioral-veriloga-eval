# LC VCO Behavioral Source

## Task Contract

Implement a Verilog-A DUT source package for a mixed-signal behavioral circuit block.

- Target artifacts: `lc_vco_behavioral_source.va`
- Public top module: `lc_vco_behavioral_source`
- Required public module: `lc_vco_behavioral_source`

The submitted source must include the target artifact and public module listed above. The public top module is the module instantiated by the evaluator; optional helper modules may be included only when they are part of the DUT source package, not testbench code.

## Public Verilog-A Interface

Declare top module `lc_vco_behavioral_source` with positional electrical ports `vctrl, enable, rst, osc_p, osc_n, freq_metric, amp_metric, valid`. All top-level ports are electrical.

The top module must expose exactly the public top-level port order above. Optional implementation-local helper modules are allowed, but no helper module is required by the public contract.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high output level.
- `vss = 0.0 V`: logic low output level.
- `vcm = 0.45 V`: output common-mode reference.
- `fmin = 5e6 Hz`: minimum behavioral oscillation frequency.
- `fmax = 25e6 Hz`: maximum behavioral oscillation frequency.
- `vth = 0.45 V`: threshold for enable and reset.
- `amplitude = 0.4 V`: enabled differential half-amplitude around `vcm`.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset or when disabled, drive both oscillator outputs to `vcm`, clear metrics, and clear `valid`.
- When enabled, clamp `vctrl` to `vss..vdd` and map it linearly to `fmin..fmax`.
- Generate complementary square-wave oscillator outputs at `vcm + amplitude` and `vcm - amplitude`.
- Drive `freq_metric` to the clamped control voltage and `amp_metric` to `amplitude` while enabled.
- Assert `valid` after two completed oscillator cycles following enable.
- This is a behavioral oscillator source and must not require an LC tank or branch-current model. On enable, restart both outputs at `vcm`; the first complementary state begins one half-period later. A control-voltage change affects the next half-period and must not retime a transition already pending.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add testbench code, Spectre decks, checker code, generated result files, debug-only ports, or pass/fail flags.

This is a DUT circuit-block task: implement the observable behavior directly and keep any optional internal decomposition solver-owned. The evaluator may use behavior checks to validate the top-level observable contract.

## Output Contract

Return exactly these complete source artifacts:

- `lc_vco_behavioral_source.va`
