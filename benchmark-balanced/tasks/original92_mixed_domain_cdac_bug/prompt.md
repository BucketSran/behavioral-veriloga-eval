The following module is supposed to be a voltage-domain SAR helper, but it was
written with a current-domain construct. Rewrite it as a pure voltage-domain
module suitable for EVAS, keeping the intent of producing a sampled residue
output on clock edges.

```verilog
module residue_stage (VDD, VSS, CLK, VIN, VOUT);
    inout VDD, VSS;
    input CLK, VIN;
    output VOUT;
    electrical VDD, VSS, CLK, VIN, VOUT;
    parameter real gain = 2.0;
    analog begin
        @(cross(V(CLK)-0.45, +1))
            I(VOUT, VSS) <+ ddt(gain * V(VIN, VSS));
    end
endmodule
```

Ports:
- `VDD`: electrical
- `VSS`: electrical
- `CLK`: electrical
- `VIN`: electrical
- `VOUT`: electrical (power rail)
- `VSS`: inout electrical (power rail)
- `CLK`: input electrical
- `VIN`: input electrical
- `VOUT`: output electrical

## Output Contract

- **File name**: output must be saved as `dut_fixed.va`
- **Module name**: the module must be named `residue_stage` (do not rename it)
- Return exactly one complete Verilog-A file in a fenced `verilog-a` code block.


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=80n maxstep=100p
```

Required public waveform columns in `tran.csv`:

- `CLK`, `VIN`, `VOUT`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

The evaluator may use a fixed reference testbench with the timing and observable names above.
Generate the requested DUT/fix so it behaves correctly under that public validation window.
