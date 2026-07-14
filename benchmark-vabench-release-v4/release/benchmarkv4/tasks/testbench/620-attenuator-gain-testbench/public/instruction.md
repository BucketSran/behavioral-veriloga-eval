# Attenuator Gain Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Attenuator Gain` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `attenuator_gain.va`:
  - Module `attenuator_gain` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `vout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `attenuator_gain` as `XDUT` with ordered public binding: vin=vin, vout=vout.

## Public Parameter Contract

- `attenuator_gain.attenuation` defaults to `0` dB; valid range: finite real value; the public contract specifically requires correct behavior at 0 dB and positive attenuation; sets the positive voltage attenuation in decibels using the standard amplitude-ratio relationship.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ZERO_DB_UNITY`: exercise and make observable: With attenuation set to 0 dB, vout continuously equals vin. Required traces: `time`, `vin`, `vout`.
- `P_DB_AMPLITUDE_RATIO`: exercise and make observable: For positive attenuation, the vout-to-vin amplitude ratio follows the standard voltage decibel attenuation relationship. Required traces: `time`, `vin`, `vout`.
- `P_POLARITY_PRESERVATION`: exercise and make observable: The attenuator preserves input polarity and introduces no inversion or offset. Required traces: `time`, `vin`, `vout`.
- `P_MONOTONIC_ATTENUATION`: exercise and make observable: For a fixed nonzero vin magnitude, increasing the nonnegative attenuation parameter cannot increase the magnitude of vout. Required traces: `time`, `vin`, `vout`.
- `P_CONTINUOUS_RESPONSE`: exercise and make observable: vout is a continuous memoryless scaled version of vin without clocking, retained state, clipping, or added delay. Required traces: `time`, `vin`, `vout`.

The required trace names are: `time`, `vin`, `vout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
