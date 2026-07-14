# Attenuator Gain Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `attenuator_gain.va`:
  - Module `attenuator_gain` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `vout` (output, electrical)

## Public Parameter Contract

- `attenuator_gain.attenuation` defaults to `0` dB; valid range: finite real value; the public contract specifically requires correct behavior at 0 dB and positive attenuation; sets the positive voltage attenuation in decibels using the standard amplitude-ratio relationship.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ZERO_DB_UNITY`: restore: With attenuation set to 0 dB, vout continuously equals vin. Required traces: `time`, `vin`, `vout`.
- `P_DB_AMPLITUDE_RATIO`: restore: For positive attenuation, the vout-to-vin amplitude ratio follows the standard voltage decibel attenuation relationship. Required traces: `time`, `vin`, `vout`.
- `P_POLARITY_PRESERVATION`: restore: The attenuator preserves input polarity and introduces no inversion or offset. Required traces: `time`, `vin`, `vout`.
- `P_MONOTONIC_ATTENUATION`: restore: For a fixed nonzero vin magnitude, increasing the nonnegative attenuation parameter cannot increase the magnitude of vout. Required traces: `time`, `vin`, `vout`.
- `P_CONTINUOUS_RESPONSE`: restore: vout is a continuous memoryless scaled version of vin without clocking, retained state, clipping, or added delay. Required traces: `time`, `vin`, `vout`.

## Modeling Constraints

- Use deterministic continuous real-valued voltage attenuation.
- Use voltage contributions and standard decibel-to-linear amplitude conversion.
- Do not use current contributions, transistor devices, retained state, testbench constants, or validation-only hooks.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `attenuator_gain.va`.
Every supplied `.va` file is editable; do not add or omit files.
