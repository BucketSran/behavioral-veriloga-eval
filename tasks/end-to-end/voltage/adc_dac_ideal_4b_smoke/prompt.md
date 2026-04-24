Write Verilog-A modules named `adc_ideal_4b` and `dac_ideal_4b`.

Create a voltage-domain ideal 4-bit ADC and 4-bit DAC pair in Verilog-A,
chain them for an ADC→DAC round-trip, then produce a minimal EVAS-compatible
Spectre testbench and run a smoke simulation.

Behavioral intent (ADC):

- inputs: `vin` (analog), `clk`, `vdd`, `vss`, `rst_n`
- outputs: 4-bit digital code `dout[3:0]`
- samples `vin` on each rising edge of `clk` (active-low reset holds code at 0)
- quantization: truncation-style, `code = floor(vin / vstep)`, clipped to [0, 15]
- `vstep = (vdd - vss) / 16`

Behavioral intent (DAC):

- inputs: 4-bit code `din[3:0]`, `vdd`, `vss`, `rst_n`
- output: `vout` (analog)
- combinational: `vout = code / 16 * vdd`

Implementation constraints:

- pure voltage-domain Verilog-A only
- EVAS-compatible syntax
- use `@(cross(...))` for clock edge detection in the ADC
- use `transition(...)` to drive digital and analog outputs
- `vin`, `clk`, `vout`, and all `dout` bits must appear in the waveform CSV

Observable contract:

- The waveform CSV must expose these exact signal names: `vin`, `clk`, `rst_n`,
  `vout`, `dout_3`, `dout_2`, `dout_1`, `dout_0`.
- If the implementation uses a bus internally, make the testbench save each bit
  under the scalar names above.

Minimum simulation goal:

- vdd=0.9 V, 1 GHz sampling clock, ramp input from 0 to vdd over 50 ns,
  reset deasserts at ~10 ns, run for 50 ns
- ADC must exercise at least 14 distinct output codes
- `vout` must stay within [0, vdd]
- quantization error (code×vstep − vin at sample instants) must be in (−lstep, 0]

Ports:

ADC module `adc_ideal_4b`:
- `vin`: input electrical
- `clk`: input electrical
- `vdd`: input electrical
- `vss`: input electrical
- `rst_n`: input electrical
- `dout[3:0]`: output electrical bus

DAC module `dac_ideal_4b`:
- `din[3:0]`: input electrical bus
- `vdd`: input electrical
- `vss`: input electrical
- `rst_n`: input electrical
- `vout`: output electrical
