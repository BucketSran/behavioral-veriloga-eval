Create four basic voltage-domain digital gate/flip-flop models in Verilog-A,
produce minimal EVAS-compatible Spectre testbenches, and run smoke simulations.

You need to implement four separate modules:

1. **AND gate** (`and_gate`): inputs A, B; output Y = A AND B
2. **OR gate** (`or_gate`): inputs A, B; output Y = A OR B
3. **NOT gate** (`not_gate`): input A; output Y = NOT A (requires VDD/VSS supply rails)
4. **D flip-flop with synchronous reset** (`dff_rst`): inputs D, CLK, RST (active-high),
   supply rails VDD/VSS; outputs Q (data), QB (complement)

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
- `A`, `B`, `Y` (for gates); `D`, `CLK`, `Q`, `QB` (for DFF) must appear in waveform CSV

Minimum simulation goal (per module):

- AND/OR/NOT: verify all combinations of inputs over 8 ns; truth table must be exact
- DFF: 20 ns run at 1 GHz (CLK period=2 ns), exercise D=0, D=1, RST=1 sequence;
  Q must follow the expected clocked sequence and QB must always be complementary
