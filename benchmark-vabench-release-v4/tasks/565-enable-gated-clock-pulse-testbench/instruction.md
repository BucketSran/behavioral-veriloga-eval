# Enable Gated Clock Pulse Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Enable Gated Clock Pulse` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `enable_gated_clock_pulse.va`:
  - Module `enable_gated_clock_pulse` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `en` (input, electrical)
    - position 2: `pulse` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `enable_gated_clock_pulse` as `XDUT` with ordered public binding: clk=clk, en=en, pulse=pulse.

## Public Parameter Contract

- `enable_gated_clock_pulse.vdd` defaults to `0.9` V; valid range: vdd > 0; sets the voltage-coded high level of pulse.
- `enable_gated_clock_pulse.vth` defaults to `0.45` V; valid range: 0 < vth < vdd; sets the logic decision threshold for clk and en.
- `enable_gated_clock_pulse.tr` defaults to `2e-11` s; valid range: tr > 0; sets the rise and fall smoothing time of pulse.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ENABLED_HIGH`: exercise and make observable: pulse approaches vdd whenever both clk and en are above vth. Required traces: `time`, `clk`, `en`, `pulse`.
- `P_DISABLED_LOW`: exercise and make observable: pulse approaches 0 V whenever either clk or en is below vth. Required traces: `time`, `clk`, `en`, `pulse`.
- `P_ENABLE_GATING`: exercise and make observable: Changing en gates the observed clock level without creating a high output while clk is logically low. Required traces: `time`, `clk`, `en`, `pulse`.
- `P_OUTPUT_LEVELS`: exercise and make observable: pulse uses voltage-coded 0 V and vdd levels with finite transition smoothing set by tr. Required traces: `time`, `pulse`.

The required trace names are: `time`, `clk`, `en`, `pulse`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
