# Pipe ADC Gain Control Loop Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

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

## Public Parameter Contract

- `pipe_adc_gain_control_loop.vlo` defaults to `0.0`; valid range: finite; overrides vlo.
- `pipe_adc_gain_control_loop.vhi` defaults to `0.9`; valid range: finite; overrides vhi.
- `pipe_adc_gain_control_loop.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `pipe_adc_gain_control_loop.gaincodeinit` defaults to `90`; valid range: finite; overrides gaincodeinit.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_GAIN_CONTROL_INITIAL_STATE`: restore: Initialize the gain-control code to `gaincodeinit` and initialize the test-DAC controls to the declared minus phase. Required traces: `time`, `clks`, `ddiff`, `din20`, `din21`, `din22`, `din23`, `din24`, `din25`, `din26`, `dom`, `dop`, `dout10`, `dout11`, `dout12`, `dout13`, `gainctrl0`, `gainctrl1`, `gainctrl2`, `gainctrl3`, `gainctrl4`, `gainctrl5`, `gainctrl6`, `gctrlcode`.
- `P_ALTERNATING_TEST_DAC_PHASES`: restore: On rising `clks`, alternate minus and plus test-DAC phases using the sampled 7-bit input code. Required traces: `time`, `clks`, `ddiff`, `din20`, `din21`, `din22`, `din23`, `din24`, `din25`, `din26`, `dom`, `dop`, `dout10`, `dout11`, `dout12`, `dout13`, `gainctrl0`, `gainctrl1`, `gainctrl2`, `gainctrl3`, `gainctrl4`, `gainctrl5`, `gainctrl6`, `gctrlcode`.
- `P_TARGET_DIFFERENCE_GAIN_UPDATE`: restore: Update the gain-control code from the plus/minus code difference using the declared target difference and correction polarity. Required traces: `time`, `clks`, `ddiff`, `din20`, `din21`, `din22`, `din23`, `din24`, `din25`, `din26`, `dom`, `dop`, `dout10`, `dout11`, `dout12`, `dout13`, `gainctrl0`, `gainctrl1`, `gainctrl2`, `gainctrl3`, `gainctrl4`, `gainctrl5`, `gainctrl6`, `gctrlcode`.
- `P_GAIN_OUTPUT_LEVELS`: restore: Gain-control and test-DAC outputs use valid voltage-coded low/high levels. Required traces: `time`, `clks`, `ddiff`, `din20`, `din21`, `din22`, `din23`, `din24`, `din25`, `din26`, `dom`, `dop`, `dout10`, `dout11`, `dout12`, `dout13`, `gainctrl0`, `gainctrl1`, `gainctrl2`, `gainctrl3`, `gainctrl4`, `gainctrl5`, `gainctrl6`, `gctrlcode`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `pipe_adc_gain_control_loop.va`.
Every supplied `.va` file is editable; do not add or omit files.
