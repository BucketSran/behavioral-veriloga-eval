# Clocked ADC3bit Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `clocked_adc3bit.va`:
  - Module `clocked_adc3bit` (entry)
    - position 0: `vd2` (output, electrical)
    - position 1: `vd1` (output, electrical)
    - position 2: `vd0` (output, electrical)
    - position 3: `vin` (input, electrical)
    - position 4: `vclk` (input, electrical)

## Public Parameter Contract

- `clocked_adc3bit.vth_clk` defaults to `0.45`; valid range: finite; overrides vth_clk.
- `clocked_adc3bit.vh` defaults to `0.9`; valid range: finite; overrides vh.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_EACH_RISING_CROSSING_OF_VCLK`: restore: On each rising crossing of `vclk` through `vth_clk`, sample `vin` and quantize the `0 V` to `1 V` range into eight uniform lower-inclusive bins. Values below `0 V` clip to code `0`; values at or above `1 V` clip to code `7`. Drive `vd2`, `vd1`, and `vd0` as the binary representation of the held sampled code using `vh` for logic one and `0 V` for logic zero. Required traces: `time`, `vclk`, `vd0`, `vd1`, `vd2`, `vin`.
- `P_VTH_CLK_0_45_V_RISING`: restore: `vth_clk = 0.45 V`: rising-edge threshold for `vclk`. Required traces: `time`, `vclk`, `vd0`, `vd1`, `vd2`, `vin`.
- `P_VH_0_9_V_LOGIC_HIGH`: restore: `vh = 0.9 V`: logic-high output level. Required traces: `time`, `vclk`, `vd0`, `vd1`, `vd2`, `vin`.
- `P_VTH_CLK_0_45_V_RISING_2`: restore: - `vth_clk = 0.45 V`: rising-edge threshold for `vclk`. - `vh = 0.9 V`: logic-high output level. Required traces: `time`, `vclk`, `vd0`, `vd1`, `vd2`, `vin`.
- `P_THE_OUTPUT_LOW_LEVEL_IS_0`: restore: The output low level is `0 V`; the public input conversion range is `0 V` to `1 V`. Required traces: `time`, `vclk`, `vd0`, `vd1`, `vd2`, `vin`.
- `P_USE_DETERMINISTIC_VOLTAGE_DOMAIN_VERILOG_A`: restore: Use deterministic voltage-domain Verilog-A and voltage contributions only. Do not emit a testbench, checker logic, out-of-band test hooks, file I/O, random behavior, current contributions, transistor-level devices, `ddt()`, `idt()`, or simulator side channels. Required traces: `time`, `vclk`, `vd0`, `vd1`, `vd2`, `vin`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `clocked_adc3bit.va`.
Every supplied `.va` file is editable; do not add or omit files.
