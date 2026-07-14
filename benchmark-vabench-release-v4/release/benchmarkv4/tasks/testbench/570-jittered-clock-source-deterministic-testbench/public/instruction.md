# Deterministic Jittered Clock Source Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Deterministic Jittered Clock Source` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `deterministic_jittered_clock.va`:
  - Module `deterministic_jittered_clock` (entry)
    - position 0: `jitter_en` (input, electrical)
    - position 1: `seed0` (input, electrical)
    - position 2: `seed1` (input, electrical)
    - position 3: `seed2` (input, electrical)
    - position 4: `seed3` (input, electrical)
    - position 5: `seed4` (input, electrical)
    - position 6: `seed5` (input, electrical)
    - position 7: `seed6` (input, electrical)
    - position 8: `seed7` (input, electrical)
    - position 9: `clk_out` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `deterministic_jittered_clock` as `XDUT` with ordered public binding: jitter_en=jitter_en, seed0=seed0, seed1=seed1, seed2=seed2, seed3=seed3, seed4=seed4, seed5=seed5, seed6=seed6, seed7=seed7, clk_out=clk_out.

## Public Parameter Contract

- `deterministic_jittered_clock.vdd` defaults to `0.9` V; valid range: vdd > 0; sets the voltage-coded clk_out high level.
- `deterministic_jittered_clock.vth` defaults to `0.45` V; valid range: 0 < vth < vdd; sets the threshold for jitter_en and all seed inputs.
- `deterministic_jittered_clock.tr` defaults to `2e-11` s; valid range: tr > 0; sets clk_out rise and fall smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_NOMINAL_CLOCK`: exercise and make observable: With jitter_en below vth, clk_out has a constant 10 ns half-period and 20 ns full period. Required traces: `time`, `jitter_en`, `clk_out`.
- `P_SEED_DECODE`: exercise and make observable: Seed7:seed0 is sampled through vth only at each output transition and interpreted as one unsigned eight-bit seed with seed7 as MSB; seed changes affect the next scheduled half-period, not the already scheduled current edge. Required traces: `time`, `jitter_en`, `seed0`, `seed1`, `seed2`, `seed3`, `seed4`, `seed5`, `seed6`, `seed7`, `clk_out`.
- `P_EDGE_MODULATION`: exercise and make observable: For edge index k, the next half-period is 10 ns plus (((seed + 3*k) modulo 5) minus 2) times 0.8 ns. Required traces: `time`, `jitter_en`, `seed0`, `seed1`, `seed2`, `seed3`, `seed4`, `seed5`, `seed6`, `seed7`, `clk_out`.
- `P_REPEATABILITY`: exercise and make observable: With constant seed and enable history, the modulo-5 half-period sequence repeats every five output transitions; identical input histories also produce the same edge-time sequence on repeated runs. Required traces: `time`, `jitter_en`, `seed0`, `seed1`, `seed2`, `seed3`, `seed4`, `seed5`, `seed6`, `seed7`, `clk_out`.
- `P_TIMING_BOUNDS`: exercise and make observable: Every jitter-enabled half-period remains within the public modulation range from 8.4 ns through 11.6 ns. Required traces: `time`, `jitter_en`, `clk_out`.
- `P_OUTPUT_LEVELS`: exercise and make observable: clk_out uses 0 V and vdd levels with finite transition smoothing set by tr. Required traces: `time`, `clk_out`.

The required trace names are: `time`, `jitter_en`, `seed0`, `seed1`, `seed2`, `seed3`, `seed4`, `seed5`, `seed6`, `seed7`, `clk_out`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
