# LDO Load Step Recovery Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `LDO Load Step Recovery` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `ldo_load_step_recovery_flow.va`:
  - Module `ldo_load_step_recovery_flow` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `out` (output, electrical)
    - position 4: `metric` (output, electrical)
    - position 5: `load_mon` (output, electrical)
    - position 6: `ctrl_mon` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `ldo_load_step_recovery_flow` as `XDUT` with ordered public binding: clk=clk, rst=rst, vin=vin, out=out, metric=metric, load_mon=load_mon, ctrl_mon=ctrl_mon.

## Public Parameter Contract

- `ldo_load_step_recovery_flow.tr` defaults to `1e-10` s; valid range: tr > 0; sets output transition smoothing.
- `ldo_load_step_recovery_flow.vth` defaults to `0.45` V; valid range: finite real; sets clock and reset logic threshold.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_REGULATION_STATE`: exercise and make observable: Active-high reset initializes out and target to 0.60 V, load_mon to 0.10 V, ctrl_mon to 0.50 V, metric to 0.9 V, and clears recovery progress. Required traces: `time`, `rst`, `out`, `metric`, `load_mon`, `ctrl_mon`.
- `P_BOUNDED_LOAD_AND_TARGET`: exercise and make observable: Each non-reset rising clk edge clips vin to 0 V through 0.9 V on load_mon and uses the public load-dependent target 0.61 V minus 0.025 times load. Required traces: `time`, `clk`, `rst`, `vin`, `load_mon`, `out`.
- `P_CONTROL_MONITOR`: exercise and make observable: Ctrl_mon represents the public load and regulation-error control expression and remains clamped to 0.05 V through 0.85 V. Required traces: `time`, `clk`, `load_mon`, `out`, `ctrl_mon`.
- `P_HEAVY_LOAD_DROOP`: exercise and make observable: A sampled load increase greater than 0.20 V causes the public 0.13 V transient droop before first-order recovery and restarts recovery qualification. Required traces: `time`, `clk`, `load_mon`, `out`, `metric`.
- `P_LIGHT_LOAD_KICK`: exercise and make observable: A sampled load decrease greater than 0.20 V causes the public 0.05 V light-load recovery kick before first-order recovery and restarts qualification. Required traces: `time`, `clk`, `load_mon`, `out`, `metric`.
- `P_RECOVERY_AND_SETTLING`: exercise and make observable: Every non-reset update applies the public 0.30 first-order recovery, clamps out to 0.20 V through 0.75 V, and sets metric high only after at least five updates with target error below 0.045 V. Required traces: `time`, `clk`, `out`, `metric`, `load_mon`.

The required trace names are: `time`, `clk`, `rst`, `vin`, `out`, `metric`, `load_mon`, `ctrl_mon`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
