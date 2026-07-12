# Correlated Double Sampler Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `correlated_double_sampler.va`:
  - Module `correlated_double_sampler` (entry)
    - position 0: `phi_reset` (input, electrical)
    - position 1: `phi_signal` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `vout` (output, electrical)
    - position 4: `valid` (output, electrical)

## Public Parameter Contract

- `correlated_double_sampler.vth` defaults to `0.45` V; valid range: vth > 0; sets the rising-edge threshold for both sampling clocks.
- `correlated_double_sampler.vcm` defaults to `0.45` V; valid range: vlo <= vcm <= vhi; sets the initial, reset-phase, and common-mode output level.
- `correlated_double_sampler.gain` defaults to `1`; valid range: any finite real; scales the sampled signal-minus-reset difference.
- `correlated_double_sampler.vlo` defaults to `0` V; valid range: vlo < vhi; sets the lower output clamp.
- `correlated_double_sampler.vhi` defaults to `0.9` V; valid range: vhi > vlo; sets the upper output clamp and valid high level.
- `correlated_double_sampler.tr` defaults to `1e-10` s; valid range: tr > 0; sets vout and valid transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_SAMPLE`: restore: A rising phi_reset crossing captures vin as the reset level, returns vout to vcm, and clears valid. Required traces: `time`, `phi_reset`, `vin`, `vout`, `valid`.
- `P_SIGNAL_CORRECTION`: restore: A rising phi_signal crossing publishes vcm plus gain times the current signal sample minus the most recently captured reset sample. Required traces: `time`, `phi_reset`, `phi_signal`, `vin`, `vout`, `valid`.
- `P_OUTPUT_CLAMP`: restore: The corrected output is limited to the inclusive vlo-to-vhi range. Required traces: `time`, `phi_signal`, `vin`, `vout`.
- `P_VALID_SEQUENCE`: restore: valid is low before a completed signal sample and after every reset sample, then rises to vhi when a signal sample is published. Required traces: `time`, `phi_reset`, `phi_signal`, `valid`.
- `P_HOLD_BETWEEN_EVENTS`: restore: vout and valid hold their last event-updated states between reset and signal sampling crossings. Required traces: `time`, `phi_reset`, `phi_signal`, `vin`, `vout`, `valid`.

## Modeling Constraints

- Use deterministic event-driven sample-and-hold state.
- Keep sampling events separate from smooth unconditional output contributions.
- Do not continuously track vin, reverse the subtraction order, or add undeclared artifacts, validation hooks, current contributions, ddt(), or idt().
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `correlated_double_sampler.va`.
Every supplied `.va` file is editable; do not add or omit files.
