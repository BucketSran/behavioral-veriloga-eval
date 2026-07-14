# Reference Startup Enable Flow Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

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

## Public Parameter Contract

- `reference_startup_enable_flow.tr` defaults to `1e-10` s; valid range: finite real; use tr >= 0 for physical transition smoothing; sets smoothing for all voltage-coded outputs.
- `reference_startup_enable_flow.vth` defaults to `0.45` V; valid range: finite real; sets clk, rst, and en decision thresholds.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_SUPPLY_AND_ENABLE_MONITORS`: restore: Supply_ok is 0.9 V exactly when vdd_in exceeds 0.32 V, while enable_mon is 0.9 V exactly when en exceeds vth. Required traces: `time`, `vdd_in`, `en`, `supply_ok`, `enable_mon`.
- `P_RESET_OR_BROWNOUT`: restore: Active reset or a bad supply clears out, metric, startup progress, and state; a supply dip also removes valid status. Required traces: `time`, `clk`, `rst`, `vdd_in`, `out`, `metric`, `state_mon`, `startup_mon`.
- `P_DISABLED_REFERENCE`: restore: With supply good and enable low, out is 0.05 V, metric is 0.1 V, startup progress is cleared, and state_mon represents state 1. Required traces: `time`, `clk`, `vdd_in`, `en`, `out`, `metric`, `state_mon`, `startup_mon`.
- `P_ENABLED_SETTLING`: restore: On each rising clk crossing with supply good and enable high, out advances by 0.32 times its remaining error to 0.55 V and the startup count increments up to 8. Required traces: `time`, `clk`, `vdd_in`, `en`, `out`, `startup_mon`.
- `P_STARTUP_VALIDITY`: restore: During enabled startup metric is 0.25 V and state is 2; after at least five enabled updates with out above 0.48 V, metric is 0.9 V and state is 3. Required traces: `time`, `clk`, `out`, `metric`, `state_mon`, `startup_mon`.
- `P_BROWNOUT_RECOVERY`: restore: After a supply dip and restoration with enable asserted, the output and monitors repeat the same startup sequence before returning valid. Required traces: `time`, `clk`, `vdd_in`, `en`, `out`, `metric`, `supply_ok`, `state_mon`, `startup_mon`.

## Modeling Constraints

- Update startup state only on rising clk crossings and derive all monitor outputs from public state.
- Use deterministic smoothed voltage contributions only.
- Do not use branch-current contributions, transistor-level devices, AC/noise analysis, KCL/KVL regulation loops, validation hooks, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `reference_startup_enable_flow.va`.
Every supplied `.va` file is editable; do not add or omit files.
