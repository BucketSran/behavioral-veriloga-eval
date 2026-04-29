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

Expected behavior:
- Reset should have highest priority over all other signals
- When rst=high: outp and outn should both be forced to defined state
- Reset should clear both outputs, not just one
Ports:
- `vdd`: electrical
- `vss`: electrical
- `clk`: electrical
- `rst`: electrical
- `inp`: electrical
- `inn`: electrical
- `outp`: electrical
- `outn`: electrical (power rail)
- `vss`: inout electrical (power rail)
- `clk`: input electrical
- `rst`: input electrical
- `inp`: input electrical
- `inn`: input electrical
- `outp`: output electrical
- `outn`: output electrical

## Output Contract

- **File name**: output must be saved as `dut_fixed.va`
- **Module name**: the module must be named `strongarm_reset_priority_fixed` (do not rename it)
- Return exactly one complete Verilog-A file in a fenced `verilog-a` code block.

Write EVAS-compatible Verilog-A (pure voltage-domain behavioral model, no current contributions).


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=80n maxstep=20p errpreset=conservative
```

Required public waveform columns in `tran.csv`:

- `time`, `rst`, `inp`, `inn`, `outp`, `outn`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

The evaluator may use a fixed reference testbench with the timing and observable names above.
Generate the requested DUT/fix so it behaves correctly under that public validation window.
