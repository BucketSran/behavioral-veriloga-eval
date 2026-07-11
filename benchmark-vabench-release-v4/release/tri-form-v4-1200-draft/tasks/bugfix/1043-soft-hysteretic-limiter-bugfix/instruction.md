# Soft Hysteretic Limiter Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `soft_hysteretic_limiter.va`:
  - Module `soft_hysteretic_limiter` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `out` (output, electrical)
    - position 4: `metric` (output, electrical)

## Public Parameter Contract

- `soft_hysteretic_limiter.tr` defaults to `1e-10` s; valid range: tr > 0; sets out and metric transition smoothing.
- `soft_hysteretic_limiter.gain` defaults to `1.8`; valid range: gain > 0; sets the sampled small-signal gain about 0.45 V common mode.
- `soft_hysteretic_limiter.hys_step` defaults to `0.08` V; valid range: hys_step >= 0; sets the signed remembered offset after upper or lower threshold excursions.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_NEUTRAL`: restore: Initialization or active reset sets out and metric to 0.45 V and clears the remembered hysteresis offset. Required traces: `time`, `clk`, `rst`, `out`, `metric`.
- `P_HYSTERESIS_STATE_UPDATE`: restore: On rising clk crossings, vin above 0.62 V stores +hys_step, vin below 0.38 V stores -hys_step, and vin within the middle band preserves the prior offset. Required traces: `time`, `clk`, `rst`, `vin`, `metric`.
- `P_GAINED_LIMITER_TRANSFER`: restore: The held output target is 0.45 V plus gain times vin minus 0.45 V plus the remembered hysteresis offset. Required traces: `time`, `clk`, `vin`, `out`, `metric`.
- `P_OUTPUT_LIMITS`: restore: Out is clamped to 0.10 V through 0.82 V with finite transition smoothing. Required traces: `time`, `out`.
- `P_STATE_METRIC`: restore: Metric equals 0.45 V plus twice the remembered offset, producing 0.61 V and 0.29 V for the default high- and low-memory states. Required traces: `time`, `clk`, `vin`, `metric`.

## Modeling Constraints

- Use deterministic event-updated voltage-domain state and finite output smoothing.
- Do not use current contributions, transistor-level devices, AC/noise analysis, ddt(), or idt().
- Do not add validation-only hooks, ports, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `soft_hysteretic_limiter.va`.
Every supplied `.va` file is editable; do not add or omit files.
