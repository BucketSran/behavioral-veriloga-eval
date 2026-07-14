# Loop Filter Abstraction Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Loop Filter Abstraction` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `loop_filter_abstraction.va`:
  - Module `loop_filter_abstraction` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `out` (output, electrical)
    - position 4: `metric` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `loop_filter_abstraction` as `XDUT` with ordered public binding: clk=clk, rst=rst, vin=vin, out=out, metric=metric.

## Public Parameter Contract

- `loop_filter_abstraction.tr` defaults to `1e-10` s; valid range: tr > 0; sets rise and fall smoothing for out and metric.
- `loop_filter_abstraction.deadband` defaults to `0.05` V; valid range: deadband >= 0; sets the sampled error magnitude below which proportional and integral state hold.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_STATE`: exercise and make observable: Active reset restores the proportional state to 0.45 V, the step to 0.20 V, the integral residual and accepted-update count to zero, and metric to 0 V. Required traces: `time`, `clk`, `rst`, `out`, `metric`.
- `P_DEADBAND_HOLD`: exercise and make observable: At a rising clk crossing, an error vin - 0.45 V whose magnitude does not exceed deadband produces no proportional, integral, step, or count update. Required traces: `time`, `clk`, `rst`, `vin`, `out`, `metric`.
- `P_SIGNED_UPDATE`: exercise and make observable: Each accepted positive error increases the proportional state by the current step and each accepted negative error decreases it, while the integral residual accumulates 0.04 times the sampled error. Required traces: `time`, `clk`, `vin`, `out`.
- `P_STEP_HALVING`: exercise and make observable: The proportional step halves after every accepted update, producing successively smaller proportional corrections for equal-sign errors. Required traces: `time`, `clk`, `vin`, `out`.
- `P_LOCK_COUNT_METRIC`: exercise and make observable: Metric remains low for fewer than four accepted updates and is 0.9 V once the accepted-update count reaches four; reset clears it. Required traces: `time`, `clk`, `rst`, `vin`, `metric`.
- `P_PROPORTIONAL_CLAMP`: exercise and make observable: The proportional state is clamped to 0.05 V through 0.85 V before the accumulated integral residual is added to form out. Required traces: `time`, `clk`, `vin`, `out`.

The required trace names are: `time`, `clk`, `rst`, `vin`, `out`, `metric`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
