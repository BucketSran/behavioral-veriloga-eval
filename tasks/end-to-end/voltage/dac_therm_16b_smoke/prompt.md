Write a Verilog-A module named `dac_therm_16b`.

Create a voltage-domain 16-bit thermometer-coded DAC in Verilog-A,
then produce a minimal EVAS-compatible Spectre testbench and run a smoke simulation.

Behavioral intent:

- a 16-bit thermometer input bus `din_therm[15:0]`
- one active-low reset `rst_n` and one analog output `vout`
- the output voltage is proportional to the count of ones in the thermometer code:
  `vout = count_of_ones(din_therm) * vstep`
- parameter `vstep` sets the voltage step per active bit (default 1.0 V)
- when `rst_n` is low, `vout` is forced to 0
- use `transition(...)` to drive `vout`

Implementation constraints:

- pure voltage-domain Verilog-A only
- EVAS-compatible syntax
- use a `for` loop or `genvar` to iterate over all 16 bits
- `rst_n` and `vout` must appear in the waveform CSV

Observable contract:

- The waveform CSV must expose these exact signal names: `rst_n`, `d15`, `d14`,
  `d13`, `d12`, `d11`, `d10`, `d9`, `d8`, `d7`, `d6`, `d5`, `d4`, `d3`, `d2`,
  `d1`, `d0`, `vout`.
- If the DUT uses a thermometer bus internally, connect and save the stimulus
  bits under the scalar names `d15` through `d0`.

Minimum simulation goal:

- vstep=1.0 V, step the thermometer code through 0 ones (0 V), 4 ones (4 V),
  8 ones (8 V), 12 ones (12 V), and 16 ones (16 V), run for 2000 ns
- at the checkpoint times, `vout` must be within ±0.1 V of the expected level
- `vout` must be monotonically non-decreasing as the code increases

Ports:
- `din_therm[15:0]`: input electrical
- `rst_n`: input electrical
- `vout`: output electrical

Implement this in Verilog-A behavioral modeling.
