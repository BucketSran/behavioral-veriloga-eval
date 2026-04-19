The following voltage-domain phase-frequency detector swaps its `up` and `dn`
responses. Fix it without changing the intended function of asserting `up` when
`ref` leads and `dn` when `div` leads.

```verilog
`include "constants.vams"
`include "disciplines.vams"

module pfd_updn_bug (VDD, VSS, ref, div, up, dn);
    inout VDD, VSS;
    input ref, div;
    output up, dn;
    electrical VDD, VSS, ref, div, up, dn;
    integer up_state, dn_state;

    analog begin
        @(initial_step) begin
            up_state = 0;
            dn_state = 0;
        end

        @(cross(V(ref, VSS) - 0.45, +1)) dn_state = 1;
        @(cross(V(div, VSS) - 0.45, +1)) up_state = 1;

        if (up_state && dn_state) begin
            up_state = 0;
            dn_state = 0;
        end

        V(up, VSS) <+ V(VDD, VSS) * transition(up_state ? 1.0 : 0.0, 0, 20p, 20p);
        V(dn, VSS) <+ V(VDD, VSS) * transition(dn_state ? 1.0 : 0.0, 0, 20p, 20p);
    end
endmodule
```
