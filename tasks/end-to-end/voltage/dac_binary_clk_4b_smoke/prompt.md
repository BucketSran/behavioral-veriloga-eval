Create a voltage-domain 4-bit clocked binary DAC in Verilog-A,
then produce a minimal EVAS-compatible Spectre testbench and run a smoke simulation.

Behavioral intent:

- four 1-bit digital inputs `DIN3` (MSB), `DIN2`, `DIN1`, `DIN0` (LSB)
- one clock input `CLK` and one analog output `AOUT`
- on each rising edge of `CLK`, sample the 4-bit input code and update `AOUT`
- transfer function: `AOUT = (8*DIN3 + 4*DIN2 + 2*DIN1 + DIN0) / 16 * vref`
- output transitions smoothly using `transition(...)` with 100 ps rise/fall

Implementation constraints:

- pure voltage-domain Verilog-A only
- EVAS-compatible syntax
- use `@(cross(...))` for clock edge detection
- use `transition(...)` to drive `AOUT`
- `CLK`, `DIN3`, `DIN2`, `DIN1`, `DIN0`, and `AOUT` must appear in the waveform CSV

Minimum simulation goal:

- vref=0.9 V, sweep all 16 codes (0 to 15) in order, one code per 40 ns clock period,
  run for 660 ns
- `AOUT` must produce at least 14 distinct output levels
- output must be monotonically non-decreasing as the input code increases
- full output range (code 0 to code 15) must span at least 75% of vref
