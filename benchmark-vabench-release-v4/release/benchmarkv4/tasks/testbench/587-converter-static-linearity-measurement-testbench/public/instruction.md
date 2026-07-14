# Converter Static Linearity Measurement Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Converter Static Linearity Measurement` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `converter_static_linearity_measurement_flow.va`:
  - Module `converter_static_linearity_measurement_flow` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `code` (output, electrical)
    - position 4: `recon` (output, electrical)
    - position 5: `dnl` (output, electrical)
    - position 6: `inl` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `converter_static_linearity_measurement_flow` as `XDUT` with ordered public binding: clk=clk, rst=rst, vin=vin, code=code, recon=recon, dnl=dnl, inl=inl.

## Public Parameter Contract

- `converter_static_linearity_measurement_flow.vth` defaults to `0.45` V; valid range: finite real; sets clock and reset logic threshold.
- `converter_static_linearity_measurement_flow.vfs` defaults to `0.9` V; valid range: vfs > 0; sets the full-scale input and code-output range.
- `converter_static_linearity_measurement_flow.tr` defaults to `1.2e-10` s; valid range: tr > 0; sets metric-output transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_STATE`: exercise and make observable: Active-high reset clears the retained conversion and previous-step state to the public reset values. Required traces: `time`, `clk`, `rst`, `code`, `recon`, `dnl`, `inl`.
- `P_FOUR_BIT_QUANTIZATION`: exercise and make observable: On each non-reset rising clk edge, vin clips to 0 through vfs and quantizes monotonically to one of 16 codes represented as code_index times vfs/15. Required traces: `time`, `clk`, `rst`, `vin`, `code`.
- `P_PUBLIC_RECONSTRUCTION_TABLE`: exercise and make observable: For each code 0 through 15, recon equals the corresponding value in the public monotonic non-ideal reconstruction table, with default table voltages scaled by vfs/0.9 for legal vfs overrides. Required traces: `time`, `clk`, `code`, `recon`.
- `P_INL_METRIC`: exercise and make observable: INL encodes reconstruction error from the vfs/15-per-code ideal ramp using the public gain and 0.05 V through 0.85 V clamp. Required traces: `time`, `code`, `recon`, `inl`.
- `P_DNL_INCREASING_STEP`: exercise and make observable: For a valid increasing code step, dnl encodes actual reconstruction-step error relative to vfs/15 per code step with the public scaling and clamp. Required traces: `time`, `clk`, `code`, `recon`, `dnl`.
- `P_DNL_NO_STEP_BASELINE`: exercise and make observable: Before a valid increasing step, or when code does not increase, dnl is held at the 0.45 V baseline. Required traces: `time`, `clk`, `code`, `recon`, `dnl`.

The required trace names are: `time`, `clk`, `rst`, `vin`, `code`, `recon`, `dnl`, `inl`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
