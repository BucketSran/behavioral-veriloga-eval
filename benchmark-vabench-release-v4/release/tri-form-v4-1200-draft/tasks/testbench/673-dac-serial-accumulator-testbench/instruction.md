# DAC Serial Accumulator Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `DAC Serial Accumulator` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `dac_serial_accumulator.va`:
  - Module `dac_serial_accumulator` (entry)
    - position 0: `clk_sample` (input, electrical)
    - position 1: `clk_sarready` (input, electrical)
    - position 2: `data` (input, electrical)
    - position 3: `out` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `dac_serial_accumulator` as `XDUT` with ordered public binding: clk_sample=clk_sample, clk_sarready=clk_sarready, data=data, out=out.

## Public Parameter Contract

- `dac_serial_accumulator.vdd` defaults to `1.1`; valid range: finite; overrides vdd.
- `dac_serial_accumulator.vcm` defaults to `0.55`; valid range: finite; overrides vcm.
- `dac_serial_accumulator.bit_count` defaults to `4`; valid range: finite; overrides bit_count.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_SAMPLE_CLOCK_RESET`: exercise and make observable: Each falling `clk_sample` crossing resets the accumulator and serial bit counter. Required traces: `time`, `clk_sample`, `out`.
- `P_SARREADY_SERIAL_ACCUMULATION`: exercise and make observable: Falling `clk_sarready` crossings during the active bit window add the sampled `data` bit to the accumulator. Required traces: `time`, `clk_sarready`, `data`, `out`.
- `P_BINARY_WEIGHT_ORDER`: exercise and make observable: The first accepted serial bit has the largest binary weight and later bits use descending weights. Required traces: `time`, `clk_sarready`, `data`, `out`.
- `P_BIPOLAR_OUTPUT_MAPPING`: exercise and make observable: The accumulated code is mapped to the required bipolar output range rather than an unipolar code. Required traces: `time`, `out`.

The required trace names are: `time`, `clk_sample`, `clk_sarready`, `data`, `out`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
