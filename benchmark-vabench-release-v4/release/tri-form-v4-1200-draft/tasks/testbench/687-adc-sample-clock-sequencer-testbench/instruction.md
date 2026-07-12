# ADC Sample Clock Sequencer Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `ADC Sample Clock Sequencer` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `adc_sample_clock_sequencer.va`:
  - Module `adc_sample_clock_sequencer` (entry)
    - position 0: `rst` (output, electrical)
    - position 1: `s` (output, electrical)
    - position 2: `ss` (output, electrical)
    - position 3: `nc_az` (output, electrical)
    - position 4: `nc` (output, electrical)
    - position 5: `conv` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `adc_sample_clock_sequencer` as `XDUT` with ordered public binding: rst=rst, s=s, ss=ss, nc_az=nc_az, nc=nc, conv=conv.

## Public Parameter Contract

- No public parameter is declared.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_PERIODIC_18NS_FRAME`: exercise and make observable: Generate a repeating 18 ns timing frame. Required traces: `time`, `conv`, `nc`, `nc_az`, `rst`, `s`, `ss`.
- `P_RESET_SAMPLE_AND_SS_WINDOWS`: exercise and make observable: `rst`, `s`, and `ss` are high only in the declared frame windows. Required traces: `time`, `conv`, `nc`, `nc_az`, `rst`, `s`, `ss`.
- `P_NONOVERLAP_AND_AUTOZERO_WINDOWS`: exercise and make observable: `nc` and `nc_az` use the declared non-overlap and autozero windows without swapping outputs. Required traces: `time`, `conv`, `nc`, `nc_az`, `rst`, `s`, `ss`.
- `P_CONVERSION_WINDOW_TIMING`: exercise and make observable: `conv` is asserted in the declared conversion windows with the correct phase. Required traces: `time`, `conv`, `nc`, `nc_az`, `rst`, `s`, `ss`.
- `P_TIMING_OUTPUT_LEVELS`: exercise and make observable: All timing outputs drive valid voltage-coded low/high levels. Required traces: `time`, `conv`, `nc`, `nc_az`, `rst`, `s`, `ss`.

The required trace names are: `time`, `conv`, `nc`, `nc_az`, `rst`, `s`, `ss`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
