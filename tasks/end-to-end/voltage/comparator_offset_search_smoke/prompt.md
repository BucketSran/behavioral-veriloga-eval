Write a pure voltage-domain Verilog-A comparator with a built-in static offset.

Requirements:

1. Ports: `vdd`, `vss`, `inp`, `inn`, `outp`
2. Built-in offset parameter `vos = 5m`
3. Output should switch high when `V(inp) - V(inn) > vos`
4. Use EVAS-compatible `cross()` events and `transition()`
5. The benchmark testbench will ramp `inp` and verify that the crossing occurs near `inn + vos`
