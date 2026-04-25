Write a voltage-domain 8-bit SAR ADC, matching weighted DAC, sample/hold helper, and one EVAS-compatible Spectre testbench.

# Task: sar_adc_dac_weighted_8b_smoke

## Objective

Create an ADC-to-DAC round-trip smoke system. The SAR ADC converts a full-swing sine input to an
8-bit code, the weighted DAC converts the code back to an analog output, and the checker verifies
code coverage and output range.

## Required Verilog-A Modules

Return these Verilog-A modules:

1. `sar_adc_weighted_8b`
   - Ports, all `electrical`, exactly in this order:
     - `vin`, `clks`, `rst_n`, `dout[7:0]`
   - On each rising `clks` edge after reset, output:
     - `code = floor(V(vin) / vdd * 255)`, clipped to `[0, 255]`
   - `dout_7` is MSB and `dout_0` is LSB in the scalar testbench connection.
2. `dac_weighted_8b`
   - Ports, all `electrical`, exactly in this order:
     - `din[7:0]`, `vout`
   - Output:
     - `vout = weighted_code / 255 * vdd`
3. `sh_ideal`
   - Ports, all `electrical`, exactly in this order:
     - `vin`, `clks`, `vdd`, `vss`, `rst_n`, `vin_sh`
   - Tracks or samples `vin` so the checker can observe the sampled input as `vin_sh`.

## Behavioral Contract

- Use pure voltage-domain Verilog-A only.
- Use `@(cross(V(clks) - vth, +1))` for clocked updates.
- Use `transition(...)` for all driven outputs.
- Output HIGH should use `vdd`; output LOW should use `0`.
- The ADC code range should cover most of `[0, 255]` under the testbench sine input.
- `vout` must stay within `[0, vdd]`.

## Testbench Contract

- Use a 0.9 V supply and 0 V reference.
- Drive `clks` with a 50 MHz-class sampling clock.
- Use active-low `rst_n` and release reset early enough to leave many post-reset samples.
- Drive `vin` with a full-swing sine input around mid-supply so the sampled input covers most ADC codes.
- Instantiate `sar_adc_weighted_8b`, `dac_weighted_8b`, and `sh_ideal` by positional scalar ports.
- Save these exact scalar names:
  - `vin`, `vin_sh`, `clks`, `rst_n`, `vout`
  - `dout_7`, `dout_6`, `dout_5`, `dout_4`, `dout_3`, `dout_2`, `dout_1`, `dout_0`
- Use the final transient setting provided by the injected Strict EVAS Validation Contract.

## Expected Checker-Visible Behavior

- Many distinct post-reset output codes should appear.
- Code range should span near the endpoints of the 8-bit range.
- `vout` should follow the code-derived DAC level and remain within the supply range.

## Deliverables

Return exactly four fenced code blocks:

1. `sar_adc_weighted_8b.va`
2. `dac_weighted_8b.va`
3. `sh_ideal.va`
4. `tb_sar_adc_dac_weighted_8b.scs`


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=10u maxstep=5n
```

Required public waveform columns in `tran.csv`:

- `vin`, `vin_sh`, `vout`, `rst_n`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Reset-like input(s) `reset`, `rst_n` must be asserted only for startup/explicit reset checks, then deasserted early enough and kept deasserted through the post-reset checking window.
- For active-low resets such as `rstb`, `rst_n`, or `rst_ni`, avoid a finite-width pulse that returns the reset node low after release; use a waveform that remains high during checking.
- Clock-like input(s) `clock` must provide enough valid edges after reset/enable for the checker to sample settled outputs.
- Sequential outputs are sampled shortly after clock edges, so drive outputs with stable held state variables and `transition()` targets rather than glitchy combinational expressions.
- Public stimulus nodes used by the reference harness include: `vdd`, `vss`, `clks`, `rst_n`, `vin`.
