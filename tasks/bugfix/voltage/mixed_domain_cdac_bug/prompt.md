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
