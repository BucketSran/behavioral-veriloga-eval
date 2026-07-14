# Clocked ADC3bit Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Clocked ADC3bit` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `clocked_adc3bit.va`:
  - Module `clocked_adc3bit` (entry)
    - position 0: `vd2` (output, electrical)
    - position 1: `vd1` (output, electrical)
    - position 2: `vd0` (output, electrical)
    - position 3: `vin` (input, electrical)
    - position 4: `vclk` (input, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `clocked_adc3bit` as `XDUT` with ordered public binding: vd2=vd2, vd1=vd1, vd0=vd0, vin=vin, vclk=vclk.

## Public Parameter Contract

- `clocked_adc3bit.vth_clk` defaults to `0.45`; valid range: finite; overrides vth_clk.
- `clocked_adc3bit.vh` defaults to `0.9`; valid range: finite; overrides vh.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_EACH_RISING_CROSSING_OF_VCLK`: exercise and make observable: On each rising crossing of `vclk` through `vth_clk`, sample `vin` and quantize the `0 V` to `1 V` range into eight uniform lower-inclusive bins. Values below `0 V` clip to code `0`; values at or above `1 V` clip to code `7`. Drive `vd2`, `vd1`, and `vd0` as the binary representation of the held sampled code using `vh` for logic one and `0 V` for logic zero. Required traces: `time`, `vclk`, `vd0`, `vd1`, `vd2`, `vin`.
- `P_VTH_CLK_0_45_V_RISING`: exercise and make observable: `vth_clk = 0.45 V`: rising-edge threshold for `vclk`. Required traces: `time`, `vclk`, `vd0`, `vd1`, `vd2`, `vin`.
- `P_VH_0_9_V_LOGIC_HIGH`: exercise and make observable: `vh = 0.9 V`: logic-high output level. Required traces: `time`, `vclk`, `vd0`, `vd1`, `vd2`, `vin`.
- `P_VTH_CLK_0_45_V_RISING_2`: exercise and make observable: - `vth_clk = 0.45 V`: rising-edge threshold for `vclk`. - `vh = 0.9 V`: logic-high output level. Required traces: `time`, `vclk`, `vd0`, `vd1`, `vd2`, `vin`.
- `P_THE_OUTPUT_LOW_LEVEL_IS_0`: exercise and make observable: The output low level is `0 V`; the public input conversion range is `0 V` to `1 V`. Required traces: `time`, `vclk`, `vd0`, `vd1`, `vd2`, `vin`.
- `P_USE_DETERMINISTIC_VOLTAGE_DOMAIN_VERILOG_A`: exercise and make observable: Use deterministic voltage-domain Verilog-A and voltage contributions only. Do not emit a testbench, checker logic, out-of-band test hooks, file I/O, random behavior, current contributions, transistor-level devices, `ddt()`, `idt()`, or simulator side channels. Required traces: `time`, `vclk`, `vd0`, `vd1`, `vd2`, `vin`.

The required trace names are: `time`, `vclk`, `vd0`, `vd1`, `vd2`, `vin`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
