# Fractional-delay DTC Macro

## Task Contract

Implement a Verilog-A DUT source package for a mixed-signal behavioral circuit block.

- Target artifacts: `fractional_delay_dtc_macro.va`
- Public top module: `fractional_delay_dtc_macro`
- Required public module: `fractional_delay_dtc_macro`

The submitted source must include the target artifact and public module listed above. The public top module is the top-level DUT entry point; optional helper modules may be included only when they are part of the returned DUT source package, not verification harness code.

## Public Verilog-A Interface

Declare top module `fractional_delay_dtc_macro` with positional electrical ports `clk_in, rst, enable, frac_3, frac_2, frac_1, frac_0, clk_out, phase_metric, valid`. All top-level ports are electrical.

The top module must expose exactly the public top-level port order above. Optional implementation-local helper modules are allowed, but no helper module is required by the public contract.

## Public Parameter Contract

Provide these overrideable public parameters on the top module and propagate compatible values to helper modules where needed:

- `vdd = 0.9 V`: logic high and upper output rail.
- `vss = 0.0 V`: logic low and lower output rail.
- `vcm = 0.45 V`: signal common-mode reference.
- `vth = 0.45 V`: threshold for voltage-coded control inputs.
- `tr = 200 ps`: output transition smoothing time.

## Required Behavior

- On reset or when disabled, clear output, phase metric, and `valid`.
- Decode `frac_3..frac_0` as a fractional delay setting.
- For each input edge, emit one output edge with a delay proportional to the fractional code.
- Expose the fractional delay as `phase_metric`.
- Preserve input-edge order and assert `valid` after the first emitted delayed edge.
- Use only voltage-domain behavioral state and voltage contributions on public electrical outputs.
- Do not expose pass/fail flags; expose only the public observable metrics named in the interface.

On each rising `clk_in` edge, latch `code = frac_0 + 2*frac_1 + 4*frac_2 + 8*frac_3` using `vth`, emit one rising output edge after `(code+1)*200 ps`, and from the accepted edge onward drive `phase_metric = vss + (vdd-vss)*code/15`.

## Modeling Constraints

Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation. Use voltage contributions for public electrical outputs. Do not instantiate transistor-level devices. Do not add verification harnesses, simulation decks, generated result files, logs, reports, debug-only ports, or pass/fail flags.

This is a DUT circuit-block task: implement the observable behavior directly and keep any optional internal decomposition solver-owned. Keep the top-level observable behavior sufficient to validate the public contract under varied stimulus conditions.

## Output Contract

Return exactly these complete source artifacts:

- `fractional_delay_dtc_macro.va`
