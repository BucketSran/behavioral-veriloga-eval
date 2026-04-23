Write a Verilog-A module named `sar_adc_weighted_8b`.

Create a voltage-domain 8-bit SAR ADC with binary-weighted successive approximation
and a matching 8-bit weighted DAC in Verilog-A, chain them for an ADC→DAC round-trip,
then produce a minimal EVAS-compatible Spectre testbench and run a smoke simulation.

Behavioral intent (SAR ADC):

- inputs: `vin` (analog), `clks` (sampling clock), `rst_n` (active-low reset)
- outputs: 8-bit code bus `dout[7:0]` (MSB=dout[7], LSB=dout[0])
- sampling phase: tracks vin while clks is LOW (sample and hold)
- conversion: on each rising edge of clks, execute successive approximation MSB-first
  using binary weights [128, 64, 32, 16, 8, 4, 2, 1], total_sum=255
- transfer function: code = floor(vin / vdd * 255), clipped to [0, 255]
- synchronous reset: when rst_n=0, clear all output bits

Behavioral intent (weighted DAC):

- inputs: `din[7:0]`, supply `vdd`
- output: `vout` (analog, combinatorial)
- transfer function: vout = sum_of_weighted_bits / 255 * vdd

Implementation constraints:

- pure voltage-domain Verilog-A only
- EVAS-compatible syntax
- use `@(cross(...))` for clock rising-edge detection
- use `transition(...)` for all outputs
- `vin`, `clks`, `rst_n`, `vout`, and representative `dout` bits must appear in the CSV

Minimum simulation goal:

- vdd=0.9 V, 500 MHz sampling clock, sine input (0.45 V offset, 0.45 V amplitude, 1 MHz),
  reset deasserts at 20 ns, run for 20 µs
- at least 200 distinct output codes must appear post-reset
- output code range must span near [0, 255] (min ≤ 10, max ≥ 245)
- `vout` must remain within [0, vdd]

Ports (SAR ADC module `sar_adc_weighted_8b`):
- `VIN`: input electrical
- `CLKS`: input electrical
- `RST_N`: input electrical
- `DOUT[7:0]`: output electrical (parameterized width)

Implement this in Verilog-A behavioral modeling.
