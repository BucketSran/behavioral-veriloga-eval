Create four basic voltage-domain digital gate/flip-flop models in Verilog-A,
produce minimal EVAS-compatible Spectre testbenches, and run smoke simulations.

You need to implement four separate modules:

1. **AND gate** (`and_gate`): inputs A, B; output Y = A AND B
2. **OR gate** (`or_gate`): inputs A, B; output Y = A OR B
3. **NOT gate** (`not_gate`): input A; output Y = NOT A (requires VDD/VSS supply rails)
4. **D flip-flop with synchronous reset** (`dff_rst`): inputs D, CLK, RST (active-high),
   supply rails VDD/VSS; outputs Q (data), QB (complement)

**Module port order (CRITICAL):**
- Modules with power pins: **VDD/VSS first**, then signal ports
- NOT gate: `module not_gate (inout VDD, inout VSS, input A, output Y);`
- DFF: `module dff_rst (inout VDD, inout VSS, input D, input CLK, input RST, output Q, output QB);`
- Modules without power: inputs first, outputs last
- AND/OR gate: `module and_gate (input A, input B, output Y);`

Behavioral intent for all modules:

- pure voltage-domain Verilog-A only
- EVAS-compatible syntax
- use `transition(...)` to drive all outputs
- gates are combinational: output updates continuously via `V() <+ transition(...)`
- DFF: samples D on rising edge of CLK; if RST=1 at clock edge, Q=0 regardless of D
- QB must always be the complement of Q

Implementation constraints:

- logic levels referenced to VDD/VSS supply rails
- threshold at VDD/2 for input level detection
- **Signal naming convention for the testbench:**
  - NOT gate: `not_a`, `not_y`
  - AND gate: `and_a`, `and_b`, `and_y`
  - OR gate: `or_a`, `or_b`, `or_y`
  - DFF: `dff_d`, `dff_clk`, `dff_rst`, `dff_q`, `dff_qb`
- These signals must appear in the waveform CSV via the `save` statement

Testbench requirements:

- Single top-level Spectre testbench with one `tran` analysis covering all modules
- Use `simulator lang=spectre` header
- Include all four modules with `ahdl_include`
- **Instance port order must match DUT module port order exactly:**
  - NOT gate: `I_not (not_vdd not_vss not_a not_y) not_gate`
  - DFF: `I_dff (dff_vdd dff_vss dff_d dff_clk dff_rst dff_q dff_qb) dff_rst`
  - AND/OR gate: `I_and (and_a and_b and_y) and_gate`
- **Do NOT use named port syntax** (e.g., `A=not_a VDD=vdd`) - use positional port order
- **Do NOT use colon-instance syntax in save statements**
- Correct: `save not_a not_y and_a and_b and_y or_a or_b or_y dff_d dff_clk dff_q dff_qb`
- Wrong: `save I_not:A I_not:Y I_and:A I_and:B I_and:Y` (Spectre rejects this)

Minimum simulation goal (per module):

- AND/OR/NOT: verify all combinations of inputs over 8 ns; truth table must be exact
- DFF: 20 ns run at 1 GHz (CLK period=2 ns), exercise D=0, D=1, RST=1 sequence;
  Q must follow the expected clocked sequence and QB must always be complementary

Expected behavior:
- AND gate: y = a & b (both high → output high)
- OR gate: y = a | b (either high → output high)
- NOT gate: y = ~a (inverse of input)
- DFF with reset: q = d on clk edge when rst=0; q=0 when rst=1
Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `D`: input electrical
- `CLK`: input electrical
- `RST`: input electrical
- `Q`: output electrical
- `QB`: output electrical
