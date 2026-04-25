The following voltage-domain sample-and-hold module updates on the wrong clock
edge. Fix it without changing the intended function of sampling on active clock
events and holding the value between samples.

```verilog
`include "constants.vams"
`include "disciplines.vams"

module sample_hold_bug (VDD, VSS, clk, in, out);
    inout VDD, VSS;
    input clk, in;
    output out;
    electrical VDD, VSS, clk, in, out;
    real sampled;

    analog begin
        @(initial_step) sampled = 0.0;
        @(cross(V(clk, VSS) - 0.45, -1))
            sampled = V(in, VSS);
        V(out, VSS) <+ transition(sampled, 0, 20p, 20p);
    end
endmodule
```

Expected behavior:
- Sample should occur on correct clock edge (rising or falling per spec)
- Wrong edge sampling leads to incorrect held values
Ports:
- `VDD`: electrical
- `VSS`: electrical
- `clk`: electrical
- `in`: electrical
- `out`: electrical (power rail)
- `VSS`: inout electrical (power rail)
- `clk`: input electrical
- `in`: input electrical
- `out`: output electrical

## Output Contract

- **File name**: output must be saved as `dut_fixed.va`
- **Module name**: the module must be named `sample_hold_bug` (do not rename it)
- Return exactly one complete Verilog-A file in a fenced `verilog-a` code block.

Write EVAS-compatible Verilog-A (pure voltage-domain behavioral model, no current contributions).


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=220n maxstep=100p
```

Required public waveform columns in `tran.csv`:

- `in`, `clk`, `out`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

The evaluator may use a fixed reference testbench with the timing and observable names above.
Generate the requested DUT/fix so it behaves correctly under that public validation window.
