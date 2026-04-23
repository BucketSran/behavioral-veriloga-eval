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
