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

Ports:
- `VDD`: electrical
- `VSS`: electrical
- `ref`: electrical
- `div`: electrical
- `up`: electrical
- `dn`: electrical (power rail)
- `VSS`: inout electrical (power rail)
- `ref`: input electrical
- `div`: input electrical
- `up`: output electrical
- `dn`: output electrical

## Output Contract

- **File name**: output must be saved as `dut_fixed.va`
- **Module name**: the module must be named `pfd_updn_bug` (do not rename it)
- Return exactly one complete Verilog-A file in a fenced `verilog-a` code block.


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=120n maxstep=50p
```

Required public waveform columns in `tran.csv`:

- `ref`, `div`, `up`, `dn`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

The evaluator may use a fixed reference testbench with the timing and observable names above.
Generate the requested DUT/fix so it behaves correctly under that public validation window.
