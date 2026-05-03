# pwl_monotonic_time

## Trigger

Use this skill when EVAS/Spectre-strict reports `spectre_strict:nonincreasing_pwl_time`.

## Rule

Spectre PWL source times must be strictly increasing. Duplicate timestamps are illegal even when they represent an ideal step.

## Repair Pattern

Nudge the later duplicate timestamp forward by a tiny epsilon at the femtosecond scale while preserving the intended waveform ordering.

## Safety Boundary

Only edit PWL time tokens. Do not change voltage values, source nodes, or transient duration.
