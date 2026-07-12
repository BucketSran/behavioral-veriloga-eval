# Reference Startup Enable Flow Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Reference Startup Enable Flow` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `reference_startup_enable_flow.va`:
  - Module `reference_startup_enable_flow` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vdd_in` (input, electrical)
    - position 3: `en` (input, electrical)
    - position 4: `out` (output, electrical)
    - position 5: `metric` (output, electrical)
    - position 6: `supply_ok` (output, electrical)
    - position 7: `enable_mon` (output, electrical)
    - position 8: `state_mon` (output, electrical)
    - position 9: `startup_mon` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `reference_startup_enable_flow` as `XDUT` with ordered public binding: clk=clk, rst=rst, vdd_in=vdd_in, en=en, out=out, metric=metric, supply_ok=supply_ok, enable_mon=enable_mon, state_mon=state_mon, startup_mon=startup_mon.

## Public Parameter Contract

- `reference_startup_enable_flow.tr` defaults to `1e-10` s; valid range: finite real; use tr >= 0 for physical transition smoothing; sets smoothing for all voltage-coded outputs.
- `reference_startup_enable_flow.vth` defaults to `0.45` V; valid range: finite real; sets clk, rst, and en decision thresholds.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_SUPPLY_AND_ENABLE_MONITORS`: exercise and make observable: Supply_ok is 0.9 V exactly when vdd_in exceeds 0.32 V, while enable_mon is 0.9 V exactly when en exceeds vth. Required traces: `time`, `vdd_in`, `en`, `supply_ok`, `enable_mon`.
- `P_RESET_OR_BROWNOUT`: exercise and make observable: Active reset or a bad supply clears out, metric, startup progress, and state; a supply dip also removes valid status. Required traces: `time`, `clk`, `rst`, `vdd_in`, `out`, `metric`, `state_mon`, `startup_mon`.
- `P_DISABLED_REFERENCE`: exercise and make observable: With supply good and enable low, out is 0.05 V, metric is 0.1 V, startup progress is cleared, and state_mon represents state 1. Required traces: `time`, `clk`, `vdd_in`, `en`, `out`, `metric`, `state_mon`, `startup_mon`.
- `P_ENABLED_SETTLING`: exercise and make observable: On each rising clk crossing with supply good and enable high, out advances by 0.32 times its remaining error to 0.55 V and the startup count increments up to 8. Required traces: `time`, `clk`, `vdd_in`, `en`, `out`, `startup_mon`.
- `P_STARTUP_VALIDITY`: exercise and make observable: During enabled startup metric is 0.25 V and state is 2; after at least five enabled updates with out above 0.48 V, metric is 0.9 V and state is 3. Required traces: `time`, `clk`, `out`, `metric`, `state_mon`, `startup_mon`.
- `P_BROWNOUT_RECOVERY`: exercise and make observable: After a supply dip and restoration with enable asserted, the output and monitors repeat the same startup sequence before returning valid. Required traces: `time`, `clk`, `vdd_in`, `en`, `out`, `metric`, `supply_ok`, `state_mon`, `startup_mon`.

The required trace names are: `time`, `clk`, `rst`, `vdd_in`, `en`, `out`, `metric`, `supply_ok`, `enable_mon`, `state_mon`, `startup_mon`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
