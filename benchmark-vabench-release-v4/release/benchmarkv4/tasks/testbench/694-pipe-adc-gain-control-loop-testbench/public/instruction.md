# Pipe ADC Gain Control Loop Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Pipe ADC Gain Control Loop` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `pipe_adc_gain_control_loop.va`:
  - Module `pipe_adc_gain_control_loop` (entry)
    - position 0: `din20` (input, electrical)
    - position 1: `din21` (input, electrical)
    - position 2: `din22` (input, electrical)
    - position 3: `din23` (input, electrical)
    - position 4: `din24` (input, electrical)
    - position 5: `din25` (input, electrical)
    - position 6: `din26` (input, electrical)
    - position 7: `clks` (input, electrical)
    - position 8: `dout10` (output, electrical)
    - position 9: `dout11` (output, electrical)
    - position 10: `dout12` (output, electrical)
    - position 11: `dout13` (output, electrical)
    - position 12: `gainctrl0` (output, electrical)
    - position 13: `gainctrl1` (output, electrical)
    - position 14: `gainctrl2` (output, electrical)
    - position 15: `gainctrl3` (output, electrical)
    - position 16: `gainctrl4` (output, electrical)
    - position 17: `gainctrl5` (output, electrical)
    - position 18: `gainctrl6` (output, electrical)
    - position 19: `ddiff` (output, electrical)
    - position 20: `dop` (output, electrical)
    - position 21: `dom` (output, electrical)
    - position 22: `gctrlcode` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `pipe_adc_gain_control_loop` as `XDUT` with ordered public binding: din20=din20, din21=din21, din22=din22, din23=din23, din24=din24, din25=din25, din26=din26, clks=clks, dout10=dout10, dout11=dout11, dout12=dout12, dout13=dout13, gainctrl0=gainctrl0, gainctrl1=gainctrl1, gainctrl2=gainctrl2, gainctrl3=gainctrl3, gainctrl4=gainctrl4, gainctrl5=gainctrl5, gainctrl6=gainctrl6, ddiff=ddiff, dop=dop, dom=dom, gctrlcode=gctrlcode.

## Public Parameter Contract

- `pipe_adc_gain_control_loop.vlo` defaults to `0.0`; valid range: finite; overrides vlo.
- `pipe_adc_gain_control_loop.vhi` defaults to `0.9`; valid range: finite; overrides vhi.
- `pipe_adc_gain_control_loop.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `pipe_adc_gain_control_loop.gaincodeinit` defaults to `90`; valid range: finite; overrides gaincodeinit.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_GAIN_CONTROL_INITIAL_STATE`: exercise and make observable: Initialize the gain-control code to `gaincodeinit` and initialize the test-DAC controls to the declared minus phase. Required traces: `time`, `clks`, `ddiff`, `din20`, `din21`, `din22`, `din23`, `din24`, `din25`, `din26`, `dom`, `dop`, `dout10`, `dout11`, `dout12`, `dout13`, `gainctrl0`, `gainctrl1`, `gainctrl2`, `gainctrl3`, `gainctrl4`, `gainctrl5`, `gainctrl6`, `gctrlcode`.
- `P_ALTERNATING_TEST_DAC_PHASES`: exercise and make observable: On rising `clks`, alternate minus and plus test-DAC phases using the sampled 7-bit input code. Required traces: `time`, `clks`, `ddiff`, `din20`, `din21`, `din22`, `din23`, `din24`, `din25`, `din26`, `dom`, `dop`, `dout10`, `dout11`, `dout12`, `dout13`, `gainctrl0`, `gainctrl1`, `gainctrl2`, `gainctrl3`, `gainctrl4`, `gainctrl5`, `gainctrl6`, `gctrlcode`.
- `P_TARGET_DIFFERENCE_GAIN_UPDATE`: exercise and make observable: Update the gain-control code from the plus/minus code difference using the declared target difference and correction polarity. Required traces: `time`, `clks`, `ddiff`, `din20`, `din21`, `din22`, `din23`, `din24`, `din25`, `din26`, `dom`, `dop`, `dout10`, `dout11`, `dout12`, `dout13`, `gainctrl0`, `gainctrl1`, `gainctrl2`, `gainctrl3`, `gainctrl4`, `gainctrl5`, `gainctrl6`, `gctrlcode`.
- `P_GAIN_OUTPUT_LEVELS`: exercise and make observable: Gain-control and test-DAC outputs use valid voltage-coded low/high levels. Required traces: `time`, `clks`, `ddiff`, `din20`, `din21`, `din22`, `din23`, `din24`, `din25`, `din26`, `dom`, `dop`, `dout10`, `dout11`, `dout12`, `dout13`, `gainctrl0`, `gainctrl1`, `gainctrl2`, `gainctrl3`, `gainctrl4`, `gainctrl5`, `gainctrl6`, `gctrlcode`.

The required trace names are: `time`, `clks`, `ddiff`, `din20`, `din21`, `din22`, `din23`, `din24`, `din25`, `din26`, `dom`, `dop`, `dout10`, `dout11`, `dout12`, `dout13`, `gainctrl0`, `gainctrl1`, `gainctrl2`, `gainctrl3`, `gainctrl4`, `gainctrl5`, `gainctrl6`, `gctrlcode`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
