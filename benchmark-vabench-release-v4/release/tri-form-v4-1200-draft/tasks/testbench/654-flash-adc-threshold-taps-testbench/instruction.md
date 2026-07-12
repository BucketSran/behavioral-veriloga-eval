# Flash ADC Threshold Taps Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Flash ADC Threshold Taps` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `flash_adc_threshold_taps.va`:
  - Module `flash_adc_threshold_taps` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `clk` (input, electrical)
    - position 2: `dout0` (output, electrical)
    - position 3: `dout1` (output, electrical)
    - position 4: `dout2` (output, electrical)
    - position 5: `dout3` (output, electrical)
    - position 6: `dout4` (output, electrical)
    - position 7: `dout5` (output, electrical)
    - position 8: `dout6` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `flash_adc_threshold_taps` as `XDUT` with ordered public binding: vin=vin, clk=clk, dout0=dout0, dout1=dout1, dout2=dout2, dout3=dout3, dout4=dout4, dout5=dout5, dout6=dout6.

## Public Parameter Contract

- `flash_adc_threshold_taps.vrefp` defaults to `0.125`; valid range: finite; overrides vrefp.
- `flash_adc_threshold_taps.vrefn` defaults to `-0.125`; valid range: finite; overrides vrefn.
- `flash_adc_threshold_taps.vl` defaults to `0.0`; valid range: finite; overrides vl.
- `flash_adc_threshold_taps.vh` defaults to `0.9`; valid range: finite; overrides vh.
- `flash_adc_threshold_taps.vth` defaults to `0.45`; valid range: finite; overrides vth.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_CLOCKED_SELECTED_THRESHOLD_TAPS`: exercise and make observable: Each rising `clk` crossing compares `vin` against the selected threshold taps and updates all thermometer outputs. Required traces: `time`, `clk`, `dout0`, `dout1`, `dout2`, `dout3`, `dout4`, `dout5`, `dout6`, `vin`.
- `P_THERMOMETER_POLARITY`: exercise and make observable: Outputs assert high when `vin` exceeds their associated threshold and low otherwise. Required traces: `time`, `clk`, `dout0`, `dout1`, `dout2`, `dout3`, `dout4`, `dout5`, `dout6`, `vin`.
- `P_OUTPUT_HIGH_LEVEL`: exercise and make observable: Asserted thermometer outputs use `vh` and inactive outputs use `vl`. Required traces: `time`, `clk`, `dout0`, `dout1`, `dout2`, `dout3`, `dout4`, `dout5`, `dout6`, `vin`.

The required trace names are: `time`, `clk`, `dout0`, `dout1`, `dout2`, `dout3`, `dout4`, `dout5`, `dout6`, `vin`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
