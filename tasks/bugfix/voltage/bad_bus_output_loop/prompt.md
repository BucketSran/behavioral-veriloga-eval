The following voltage-domain DUT intends to drive a 4-bit bus, but the output
assignment is incorrect. Fix it without changing the module intent.

```verilog
module bin4_out (VDD, VSS, CODE, DOUT);
    inout VDD, VSS;
    input [3:0] CODE;
    output [3:0] DOUT;
    electrical VDD, VSS;
    electrical [3:0] CODE, DOUT;
    integer i;
    analog begin
        for (i = 0; i < 4; i = i + 1)
            V(DOUT) <+ ((V(CODE[i]) > 0.45) ? V(VDD) : V(VSS));
    end
endmodule
```

Ports:
- `VDD`: electrical
- `VSS`: electrical
- `CODE`: electrical
- `DOUT`: electrical (power rail)
- `VSS`: inout electrical (power rail)
- `CODE`: unknown (electrical)
- `DOUT`: unknown (electrical)

## Output Contract

- **File name**: output must be saved as `dut_fixed.va`
- **Module name**: the module must be named `bin4_out` (do not rename it)
- Return exactly one complete Verilog-A file in a fenced `verilog-a` code block.


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=200n maxstep=100p
```

Required public waveform columns in `tran.csv`:

- `CODE_0`, `CODE_1`, `CODE_2`, `CODE_3`, `DOUT_0`, `DOUT_1`, `DOUT_2`, `DOUT_3`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

The evaluator may use a fixed reference testbench with the timing and observable names above.
Generate the requested DUT/fix so it behaves correctly under that public validation window.
