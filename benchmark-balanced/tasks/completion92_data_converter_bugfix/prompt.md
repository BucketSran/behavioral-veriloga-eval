Fix a Verilog-A implementation for the core function below without changing its public behavior.
Return the corrected Verilog-A artifact requested by the benchmark.

Core function family: data-converter.
Balanced task-form completion derived from original task: `adc_dac_ideal_4b_smoke`.

Spectre/Verilog-A compatibility requirements:
- Use voltage-domain electrical ports where applicable.
- Keep the public interface and saved observable behavior compatible with the evaluation harness.
- Prefer explicit `transition(...)` on driven voltage outputs.
- Avoid current contributions, `ddt()`, `idt()`, simulator control blocks, and non-Spectre syntax.

Source behavioral specification:

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


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=50n maxstep=100p
```

Required public waveform columns in `tran.csv`:

- `vin`, `vout`, `rst_n`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Reset-like input(s) `reset`, `rst_n` must be asserted only for startup/explicit reset checks, then deasserted early enough and kept deasserted through the post-reset checking window.
- For active-low reset inputs, avoid a finite-width pulse that returns the reset node low after release; use a waveform that remains high during checking.
- Clock-like input(s) `clk`, `clock` must provide enough valid edges after reset/enable for the checker to sample settled outputs.
- Sequential outputs are sampled shortly after clock edges, so drive outputs with stable held state variables and `transition()` targets rather than glitchy combinational expressions.
- Public stimulus nodes used by the reference harness include: `vdd`, `vss`, `clk`, `rst_n`, `vin`.
