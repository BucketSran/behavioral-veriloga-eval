# Correlated Double Sampler Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Correlated Double Sampler` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `correlated_double_sampler.va`:
  - Module `correlated_double_sampler` (entry)
    - position 0: `phi_reset` (input, electrical)
    - position 1: `phi_signal` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `vout` (output, electrical)
    - position 4: `valid` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `correlated_double_sampler` as `XDUT` with ordered public binding: phi_reset=phi_reset, phi_signal=phi_signal, vin=vin, vout=vout, valid=valid.

## Public Parameter Contract

- `correlated_double_sampler.vth` defaults to `0.45` V; valid range: vth > 0; sets the rising-edge threshold for both sampling clocks.
- `correlated_double_sampler.vcm` defaults to `0.45` V; valid range: vlo <= vcm <= vhi; sets the initial, reset-phase, and common-mode output level.
- `correlated_double_sampler.gain` defaults to `1`; valid range: any finite real; scales the sampled signal-minus-reset difference.
- `correlated_double_sampler.vlo` defaults to `0` V; valid range: vlo < vhi; sets the lower output clamp.
- `correlated_double_sampler.vhi` defaults to `0.9` V; valid range: vhi > vlo; sets the upper output clamp and valid high level.
- `correlated_double_sampler.tr` defaults to `1e-10` s; valid range: tr > 0; sets vout and valid transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_SAMPLE`: exercise and make observable: A rising phi_reset crossing captures vin as the reset level, returns vout to vcm, and clears valid. Required traces: `time`, `phi_reset`, `vin`, `vout`, `valid`.
- `P_SIGNAL_CORRECTION`: exercise and make observable: A rising phi_signal crossing publishes vcm plus gain times the current signal sample minus the most recently captured reset sample. Required traces: `time`, `phi_reset`, `phi_signal`, `vin`, `vout`, `valid`.
- `P_OUTPUT_CLAMP`: exercise and make observable: The corrected output is limited to the inclusive vlo-to-vhi range. Required traces: `time`, `phi_signal`, `vin`, `vout`.
- `P_VALID_SEQUENCE`: exercise and make observable: valid is low before a completed signal sample and after every reset sample, then rises to vhi when a signal sample is published. Required traces: `time`, `phi_reset`, `phi_signal`, `valid`.
- `P_HOLD_BETWEEN_EVENTS`: exercise and make observable: vout and valid hold their last event-updated states between reset and signal sampling crossings. Required traces: `time`, `phi_reset`, `phi_signal`, `vin`, `vout`, `valid`.

The required trace names are: `time`, `phi_reset`, `phi_signal`, `vin`, `vout`, `valid`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
