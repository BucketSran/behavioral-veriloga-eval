Write a pure voltage-domain Verilog-A parallel-to-serial block with explicit frame alignment signaling.

Module name: `serializer_frame_alignment_ref`.

Requirements:

1. Ports: `vdd`, `vss`, `clk`, `load`, `din[7:0]`, `sout`, `frame`
2. Latch parallel input word when `load` is high at a clock edge
3. Shift data out MSB-first on following clock edges
4. Assert `frame` for the first serialized bit of each loaded word
5. Use EVAS-compatible `cross()` and `transition()` style
6. Keep implementation in pure electrical voltage domain

Ports:
- `vdd`: electrical
- `vss`: electrical
- `clk`: electrical
- `load`: electrical
- `din7`: electrical
- `din6`: electrical
- `din5`: electrical
- `din4`: electrical
- `din3`: electrical
- `din2`: electrical
- `din1`: electrical
- `din0`: electrical
- `sout`: electrical
- `frame`: electrical (power rail)
- `vss`: inout electrical (power rail)
- `clk`: input electrical
- `load`: input electrical
- `din7`: input electrical
- `din6`: input electrical
- `din5`: input electrical
- `din4`: input electrical
- `din3`: input electrical
- `din2`: input electrical
- `din1`: input electrical
- `din0`: input electrical
- `sout`: output electrical
- `frame`: output electrical

## Output Contract (MANDATORY)

- Return exactly two fenced code blocks:
  - first block: Verilog-A DUT (` ```verilog-a ... ``` `)
  - second block: Spectre testbench (` ```spectre ... ``` `)
- The Spectre testbench must include the DUT with `ahdl_include "<module>.va"`.
- Use a single `tran` analysis and include the required `save` signals for checker evaluation.
