Write exactly one EVAS/Spectre-compatible Verilog-A module named `sc_integrator`.

Required module signature:

```verilog
module sc_integrator(VDD, VSS, VIN, PHI1, PHI2, VOUT);
```

The reference testbench instantiates the DUT as:

```spectre
XDUT (VDD VSS VIN PHI1 PHI2 VOUT) sc_integrator Cin=1.0 Cfb=1.0
```

Interface requirements:

- Keep the exact module name `sc_integrator`.
- Keep the exact port order: `VDD, VSS, VIN, PHI1, PHI2, VOUT`.
- Declare `VDD` and `VSS` as electrical supply/reference nodes.
- Declare `VIN`, `PHI1`, and `PHI2` as electrical inputs.
- Declare `VOUT` as an electrical output.
- Support parameters `Cin` and `Cfb`.

Behavioral intent:

- Model a non-overlapping two-phase switched-capacitor integrator.
- On the rising edge of `PHI1`, sample `VIN` relative to `VSS`.
- On the rising edge of `PHI2`, update the output state by adding `(Cin / Cfb) * sampled_vin`.
- Drive `VOUT` relative to `VSS` using a continuous voltage contribution.
- The reference stimulus uses a 0.9 V supply and non-overlapping 50 MHz phase clocks.

Compatibility constraints:

- Use pure voltage-domain Verilog-A only.
- Put initialization inside `@(initial_step)` within an `analog begin` block.
- ..))` for `PHI1` and `PHI2` edge detection.
- Do not use Verilog `initial begin` blocks.
- Do not place `transition(...)` contributions inside conditionally executed `if/else begin` branches.
- Keep any `transition(...)` contribution as a continuous contribution in the main analog block.

Ports:
- `VDD`: electrical
- `VSS`: electrical
- `VIN`: electrical
- `PHI1`: electrical
- `PHI2`: electrical
- `VOUT`: electrical (power rail)
- `VSS`: inout electrical (power rail)
- `VIN`: input electrical
- `PHI1`: input electrical
- `PHI2`: input electrical
- `VOUT`: output electrical


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=120n maxstep=100p
```

Required public waveform columns in `tran.csv`:

- `VIN`, `PHI1`, `PHI2`, `VOUT`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

The evaluator may use a fixed reference testbench with the timing and observable names above.
Generate the requested DUT/fix so it behaves correctly under that public validation window.
