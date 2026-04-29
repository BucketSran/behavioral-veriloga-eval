Create four basic voltage-domain digital gate/flip-flop models in Verilog-A
and one minimal EVAS-compatible Spectre testbench that exercises all four
modules in a single transient run.

Return exactly five fenced code blocks:

1. A `verilog-a` block for module `and_gate`
2. A `verilog-a` block for module `or_gate`
3. A `verilog-a` block for module `not_gate`
4. A `verilog-a` block for module `dff_rst`
5. A `spectre` block for the combined testbench

Do not include prose outside the code blocks.

## Required Verilog-A Modules

1. AND gate:
   - Module name: `and_gate`
   - Positional port order: `(A, B, Y)`
   - Behavior: `Y = A AND B`

2. OR gate:
   - Module name: `or_gate`
   - Positional port order: `(A, B, Y)`
   - Behavior: `Y = A OR B`

3. NOT gate:
   - Module name: `not_gate`
   - Positional port order: `(VDD, VSS, A, Y)`
   - Behavior: `Y = NOT A`

4. D flip-flop with synchronous reset:
   - Module name: `dff_rst`
   - Positional port order: `(VDD, VSS, D, CLK, RST, Q, QB)`
   - Behavior: sample `D` on the rising edge of `CLK`; when `RST` is high at
     the clock edge, force `Q=0`; `QB` is always the complement of `Q`.

## Verilog-A Requirements

- Use pure voltage-domain Verilog-A only.
- Declare all ports as `electrical`.
- Use `transition(...)` for driven outputs.
- Use Spectre-compatible Verilog-A syntax rather than digital-Verilog syntax.
- Use a threshold near half supply to detect logic levels.

## Required Testbench Structure

The Spectre testbench must include all four generated module files:

- `ahdl_include "and_gate.va"`
- `ahdl_include "or_gate.va"`
- `ahdl_include "not_gate.va"`
- `ahdl_include "dff_rst.va"`

Instantiate by positional port order:

- `I_and (and_a and_b and_y) and_gate`
- `I_or (or_a or_b or_y) or_gate`
- `I_not (not_vdd not_vss not_a not_y) not_gate`
- `I_dff (dff_vdd dff_vss dff_d dff_clk dff_rst dff_q dff_qb) dff_rst`

Use one transient analysis:

- `tran tran stop=200n maxstep=100p`

Save all public waveform columns:

- `not_a`, `not_y`
- `and_a`, `and_b`, `and_y`
- `or_a`, `or_b`, `or_y`
- `dff_d`, `dff_clk`, `dff_rst`, `dff_q`, `dff_qb`

Use plain scalar save names and Spectre-compatible instance/save syntax.

## Public Evaluation Contract

The evaluator checks the AND, OR, NOT, and DFF/reset behavior through the saved
waveform columns above. The testbench must exercise all input combinations for
the combinational gates and enough clock edges after reset for the DFF output
sequence to be visible.
