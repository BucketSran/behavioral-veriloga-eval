# DAC Mismatch Unit Weighting Model Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `DAC Mismatch Unit Weighting Model` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `dac_mismatch_unit_weighting_model.va`:
  - Module `dac_mismatch_unit_weighting_model` (entry)
    - position 0: `b0` (input, electrical)
    - position 1: `b1` (input, electrical)
    - position 2: `b2` (input, electrical)
    - position 3: `b3` (input, electrical)
    - position 4: `out` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `dac_mismatch_unit_weighting_model` as `XDUT` with ordered public binding: b0=b0, b1=b1, b2=b2, b3=b3, out=out.

## Public Parameter Contract

- `dac_mismatch_unit_weighting_model.vhi` defaults to `0.9` V; valid range: vhi > vlo; sets the all-active output endpoint.
- `dac_mismatch_unit_weighting_model.vlo` defaults to `0.0` V; valid range: vlo < vhi; sets the all-zero output endpoint.
- `dac_mismatch_unit_weighting_model.tr` defaults to `1e-10` s; valid range: tr > 0; sets output transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ZERO_AND_FULL_SCALE`: exercise and make observable: All-zero input maps to vlo and all-active input maps to vhi after transition settling. Required traces: `time`, `b0`, `b1`, `b2`, `b3`, `out`.
- `P_NONIDEAL_WEIGHT_SUM`: exercise and make observable: Inputs b0 through b3 contribute fixed positive weights 1.00, 2.02, 3.96, and 8.08 normalized by their all-active sum. Required traces: `time`, `b0`, `b1`, `b2`, `b3`, `out`.
- `P_LOGIC_THRESHOLD`: exercise and make observable: Each bit is independently interpreted using the public fixed 0.45 V decision threshold. Required traces: `time`, `b0`, `b1`, `b2`, `b3`, `out`.
- `P_BOUNDED_OUTPUT`: exercise and make observable: For every input pattern, the settled output remains within the vlo-to-vhi interval. Required traces: `time`, `b0`, `b1`, `b2`, `b3`, `out`.
- `P_MISMATCH_OBSERVABILITY`: exercise and make observable: Single-bit output increments preserve the stated nonideal weighting rather than ideal powers-of-two weighting. Required traces: `time`, `b0`, `b1`, `b2`, `b3`, `out`.

The required trace names are: `time`, `b0`, `b1`, `b2`, `b3`, `out`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
