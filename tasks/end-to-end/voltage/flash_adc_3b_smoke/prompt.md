Write a Verilog-A module named `flash_adc_3b` and one minimal EVAS-compatible Spectre testbench.

# Task: flash_adc_3b_smoke

## Objective

Create a pure voltage-domain 3-bit flash ADC behavioral model. The testbench must sweep the input
across the full reference range and produce all 8 output codes after clocked sampling.

## DUT Contract

- Module name: `flash_adc_3b`
- Ports, all `electrical`, exactly in this order: `vdd`, `vss`, `vin`, `clk`, `dout2`, `dout1`, `dout0`
- Parameters:
  - `vrefp` real, default `0.9`
  - `vrefn` real, default `0.0`
  - `vth` real, default `0.45`
  - `tedge` real, default `100p`
- Behavior:
  - On each rising `clk` edge, compute a 3-bit code from `V(vin)`.
  - Full-scale range is `vrefn` to `vrefp`, divided into 8 equal bins.
  - Clamp the code to `[0, 7]`.
  - Drive `dout2` as MSB, `dout1`, and `dout0` as LSB.
  - Output HIGH should be `V(vdd)` and output LOW should be `V(vss)`.
  - Use `@(cross(V(clk) - vth, +1))` and `transition(...)`.

## Testbench Contract

- Use a 0.9 V supply and 0 V reference.
- Drive `vin` with a monotonic full-scale sweep from near `0` to near `0.9 V` within the final validation window.
- Drive `clk` with a pulse clock fast enough to sample all 8 ADC codes during the input sweep.
- Instantiate the DUT by positional ports.
- Save these exact scalar names: `vin`, `clk`, `dout2`, `dout1`, `dout0`.
- Include the generated DUT file `flash_adc_3b.va`.
- Use the final transient setting provided by the injected Strict EVAS Validation Contract.

## Deliverables

Return exactly two fenced code blocks:

1. `flash_adc_3b.va`
2. `tb_flash_adc_3b.scs`


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=820n maxstep=2n
```

Required public waveform columns in `tran.csv`:

- `vin`, `clk`, `dout2`, `dout1`, `dout0`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Clock-like input(s) `clk`, `clock` must provide enough valid edges after reset/enable for the checker to sample settled outputs.
- Sequential outputs are sampled shortly after clock edges, so drive outputs with stable held state variables and `transition()` targets rather than glitchy combinational expressions.
- Public stimulus nodes used by the reference harness include: `vdd`, `vss`, `vin`, `clk`.
