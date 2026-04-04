Create a voltage-domain 8-bit SAR ADC with binary-weighted successive approximation
and a matching 8-bit weighted DAC in Verilog-A, chain them for an ADC→DAC round-trip,
then produce a minimal EVAS-compatible Spectre testbench and run a smoke simulation.

Behavioral intent (SAR ADC):

- inputs: `VIN` (analog), `CLKS` (sampling clock), `RST_N` (active-low reset)
- outputs: 8-bit code bus `DOUT[7:0]` (MSB=DOUT[7], LSB=DOUT[0])
- sampling phase: tracks VIN while CLKS is LOW (sample and hold)
- conversion: on each rising edge of CLKS, execute successive approximation MSB-first
  using binary weights [128, 64, 32, 16, 8, 4, 2, 1], total_sum=255
- transfer function: code = floor(vin / vdd * 255), clipped to [0, 255]
- synchronous reset: when RST_N=0, clear all output bits

Behavioral intent (weighted DAC):

- inputs: `DIN[7:0]`, supply `vdd`
- output: `vout` (analog, combinatorial)
- transfer function: vout = sum_of_weighted_bits / 255 * vdd

Implementation constraints:

- pure voltage-domain Verilog-A only
- EVAS-compatible syntax
- use `@(cross(...))` for clock rising-edge detection
- use `transition(...)` for all outputs
- `VIN`, `CLKS`, `RST_N`, `VOUT`, and representative `DOUT` bits must appear in the CSV

Minimum simulation goal:

- vdd=0.9 V, 500 MHz sampling clock, sine input (0.45 V offset, 0.45 V amplitude, 1 MHz),
  reset deasserts at 20 ns, run for 20 µs
- at least 200 distinct output codes must appear post-reset
- output code range must span near [0, 255] (min ≤ 10, max ≥ 245)
- `vout` must remain within [0, vdd]
