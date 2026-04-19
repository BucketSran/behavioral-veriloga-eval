The following voltage-domain StrongArm-style comparator has a reset-priority bug:
when `rst=1`, clock edges can still update the outputs. Fix it so reset always
forces both outputs low, and normal comparison only resumes after reset is
released.

```verilog
`include "constants.vams"
`include "disciplines.vams"

module strongarm_reset_priority_buggy(vdd, vss, clk, rst, inp, inn, outp, outn);
    inout vdd, vss;
    input clk, rst, inp, inn;
    output outp, outn;
    electrical vdd, vss, clk, rst, inp, inn, outp, outn;

    parameter real vth = 0.45;
    parameter real trf = 20p;

    integer outp_state, outn_state;

    analog begin
        @(initial_step) begin
            outp_state = 0;
            outn_state = 0;
        end

        // Bug: no reset-priority handling here.
        @(cross(V(clk, vss) - vth, +1)) begin
            if (V(inp, vss) > V(inn, vss)) begin
                outp_state = 1;
                outn_state = 0;
            end else begin
                outp_state = 0;
                outn_state = 1;
            end
        end

        V(outp, vss) <+ V(vdd, vss) * transition(outp_state ? 1.0 : 0.0, 0, trf, trf);
        V(outn, vss) <+ V(vdd, vss) * transition(outn_state ? 1.0 : 0.0, 0, trf, trf);
    end
endmodule
```

Return a fixed voltage-domain Verilog-A module that preserves the intended
StrongArm comparison behavior, but gives `rst` unconditional priority.
