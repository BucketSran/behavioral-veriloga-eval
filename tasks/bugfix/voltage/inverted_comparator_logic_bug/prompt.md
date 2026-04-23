The following voltage-domain comparator drives the output with inverted logic.
Fix it without changing the intended function of reporting whether `vinp` is
greater than `vinn`.

```verilog
`include "constants.vams"
`include "disciplines.vams"

module cmp_polarity_bug (VDD, VSS, vinp, vinn, out_p);
    inout VDD, VSS;
    input vinp, vinn;
    output out_p;
    electrical VDD, VSS, vinp, vinn, out_p;

    analog begin
        V(out_p, VSS) <+ V(VDD, VSS) * transition(
            (V(vinp, VSS) < V(vinn, VSS)) ? 1.0 : 0.0,
            0, 20p, 20p
        );
    end
endmodule
```

Expected behavior:
- Comparator output polarity should match specification
- When vinp > vinn: out_p should be high (not inverted)
- Output logic should not be reversed
Ports:
- `VDD`: electrical
- `VSS`: electrical
- `vinp`: electrical
- `vinn`: electrical
- `out_p`: electrical (power rail)
- `VSS`: inout electrical (power rail)
- `vinp`: input electrical
- `vinn`: input electrical
- `out_p`: output electrical

## Output Contract

- **File name**: output must be saved as `dut_fixed.va`
- **Module name**: the module must be named `cmp_polarity_bug` (do not rename it)
- Return exactly one complete Verilog-A file in a fenced `verilog-a` code block.

Write EVAS-compatible Verilog-A (pure voltage-domain behavioral model, no current contributions).
