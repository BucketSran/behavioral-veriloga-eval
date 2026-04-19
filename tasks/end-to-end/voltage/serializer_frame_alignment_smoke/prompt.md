Write a pure voltage-domain Verilog-A parallel-to-serial block with explicit frame alignment signaling.

Requirements:

1. Ports: `vdd`, `vss`, `clk`, `load`, `din[7:0]`, `sout`, `frame`
2. Latch parallel input word when `load` is high at a clock edge
3. Shift data out MSB-first on following clock edges
4. Assert `frame` for the first serialized bit of each loaded word
5. Use EVAS-compatible `cross()` and `transition()` style
6. Keep implementation in pure electrical voltage domain
