# Multiphase Clock Generator 4ph Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Multiphase Clock Generator 4ph` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `multiphase_clock_generator_4ph.va`:
  - Module `multiphase_clock_generator_4ph` (entry)
    - position 0: `vss` (input, electrical)
    - position 1: `clk0` (output, electrical)
    - position 2: `clk90` (output, electrical)
    - position 3: `clk180` (output, electrical)
    - position 4: `clk270` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `multiphase_clock_generator_4ph` as `XDUT` with ordered public binding: vss=0, clk0=clk0, clk90=clk90, clk180=clk180, clk270=clk270.

## Public Parameter Contract

- `multiphase_clock_generator_4ph.vdd` defaults to `0.9` V; valid range: vdd > 0; sets the high level of all four clock outputs.
- `multiphase_clock_generator_4ph.tr` defaults to `2e-11` s; valid range: tr > 0; sets rise and fall smoothing for all clock outputs.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_PERIOD`: exercise and make observable: Each output repeats with a 20 ns period. Required traces: `time`, `clk0`, `clk90`, `clk180`, `clk270`.
- `P_DUTY_CYCLE`: exercise and make observable: Each output has approximately 50 percent duty cycle. Required traces: `time`, `clk0`, `clk90`, `clk180`, `clk270`.
- `P_PHASE_OFFSETS`: exercise and make observable: Relative to clk0, corresponding rising edges of clk90, clk180, and clk270 lag by 5 ns, 10 ns, and 15 ns respectively. Required traces: `time`, `clk0`, `clk90`, `clk180`, `clk270`.
- `P_PHASE_STABILITY`: exercise and make observable: The output phase ordering and offsets remain stable across repeated periods. Required traces: `time`, `clk0`, `clk90`, `clk180`, `clk270`.
- `P_OUTPUT_LEVELS`: exercise and make observable: All clocks use 0 V and vdd levels with finite transition smoothing set by tr. Required traces: `time`, `clk0`, `clk90`, `clk180`, `clk270`.

The required trace names are: `time`, `clk0`, `clk90`, `clk180`, `clk270`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
