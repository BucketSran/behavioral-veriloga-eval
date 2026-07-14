# Sample And Hold With Droop Leakage Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `leaky_hold.va`:
  - Module `leaky_hold` (entry)
    - position 0: `sample` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `vout` (output, electrical)

## Public Parameter Contract

- `leaky_hold.vth` defaults to `0.45` V; valid range: vth > 0; sets sample and rst voltage-coded logic threshold.
- `leaky_hold.decay` defaults to `0.985`; valid range: 0 < decay <= 1; sets the multiplicative held-value retention factor per leakage update.
- `leaky_hold.leak_period` defaults to `1e-09` s; valid range: leak_period > 0; sets the periodic leakage update interval.
- `leaky_hold.tr` defaults to `5e-10` s; valid range: tr > 0; sets vout transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_SAMPLE_CAPTURE`: restore: Each rising sample crossing while reset is inactive captures the instantaneous vin voltage into the held state. Required traces: `time`, `sample`, `rst`, `vin`, `vout`.
- `P_HOLD_BETWEEN_EVENTS`: restore: Between sample and leakage events, vout reflects the retained held state rather than continuously tracking vin. Required traces: `time`, `sample`, `vin`, `vout`.
- `P_PERIODIC_DROOP`: restore: At every leak_period update while reset is inactive, the held value is multiplied by decay. Required traces: `time`, `rst`, `vout`.
- `P_RESET_CLEAR`: restore: Active reset clears the held state to 0 V at sampling or leakage update events. Required traces: `time`, `sample`, `rst`, `vout`.
- `P_SMOOTH_OUTPUT`: restore: Vout approaches each held-state target with the finite transition smoothing set by tr. Required traces: `time`, `vout`.

## Modeling Constraints

- Use deterministic event-driven voltage-domain sample and leakage updates.
- Use voltage contributions only; do not use current contributions, ddt(), or idt().
- Do not add validation hooks, hidden observables, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `leaky_hold.va`.
Every supplied `.va` file is editable; do not add or omit files.
