# Windowed Event Rate Monitor Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `windowed_event_rate_monitor.va`:
  - Module `windowed_event_rate_monitor` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `event_in` (input, electrical)
    - position 3: `gate` (input, electrical)
    - position 4: `rate` (output, electrical)
    - position 5: `average` (output, electrical)

## Public Parameter Contract

- `windowed_event_rate_monitor.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `windowed_event_rate_monitor.vhi` defaults to `0.9`; valid range: finite; overrides vhi.
- `windowed_event_rate_monitor.window_count` defaults to `5`; valid range: finite; overrides window_count.
- `windowed_event_rate_monitor.tr` defaults to `60p`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_INITIALIZE_EVENT_COUNT_SAMPLE_COUNT_RATE`: restore: Initialize `event_count`, `sample_count`, `rate`, and `average` to zero. On each rising clock crossing, clear the measurement window and both observables when `rst` is high or `gate <= vth`. Otherwise increment `sample_count`, increment `event_count` when `event_in > vth`, and drive `rate = vhi * clip01(event_count / window_count)`. Required traces: `time`, `average`, `clk`, `event_in`, `gate`, `rate`, `rst`.
- `P_FOR_THE_SAME_GATED_SAMPLE_WINDOW`: restore: For the same gated sample window, drive `average = vhi * clip01(event_count / sample_count)`. Hold the last observable values between rising clock crossings. Required traces: `time`, `average`, `clk`, `event_in`, `gate`, `rate`, `rst`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `windowed_event_rate_monitor.va`.
Every supplied `.va` file is editable; do not add or omit files.
