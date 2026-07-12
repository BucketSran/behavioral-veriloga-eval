# Linearity RDAC Offset Sweep Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Linearity RDAC Offset Sweep` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `linearity_rdac_offset_sweep.va`:
  - Module `linearity_rdac_offset_sweep` (entry)
    - position 0: `ck` (input, electrical)
    - position 1: `d` (input, electrical)
    - position 2: `vinp` (output, electrical)
    - position 3: `vinn` (output, electrical)
    - position 4: `vrefp` (output, electrical)
    - position 5: `vrefn` (output, electrical)
    - position 6: `dc0` (output, electrical)
    - position 7: `dc1` (output, electrical)
    - position 8: `dc2` (output, electrical)
    - position 9: `dc3` (output, electrical)
    - position 10: `dc4` (output, electrical)
    - position 11: `dc5` (output, electrical)
    - position 12: `dc6` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `linearity_rdac_offset_sweep` as `XDUT` with ordered public binding: ck=ck, d=d, vinp=vinp, vinn=vinn, vrefp=vrefp, vrefn=vrefn, dc0=dc0, dc1=dc1, dc2=dc2, dc3=dc3, dc4=dc4, dc5=dc5, dc6=dc6.

## Public Parameter Contract

- `linearity_rdac_offset_sweep.vcm` defaults to `0.6`; valid range: finite; overrides vcm.
- `linearity_rdac_offset_sweep.vppd` defaults to `1.0`; valid range: finite; overrides vppd.
- `linearity_rdac_offset_sweep.vdd` defaults to `1.0`; valid range: finite; overrides vdd.
- `linearity_rdac_offset_sweep.nlvl` defaults to `17.0`; valid range: finite; overrides nlvl.
- `linearity_rdac_offset_sweep.iter_num` defaults to `4`; valid range: finite; overrides iter_num.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_CLOCKED_SWEEP_DIRECTION`: exercise and make observable: Rising `ck` crossings implement the RDAC sweep using `d < 0.5*vdd` as the low comparator direction. Required traces: `time`, `ck`, `d`, `dc0`, `dc1`, `dc2`, `dc3`, `dc4`, `dc5`, `dc6`, `vinn`, `vinp`, `vrefn`, `vrefp`.
- `P_SWEEP_INITIAL_STATE`: exercise and make observable: Initialize `vref`, `vin`, search step, and stored comparator direction to the declared sweep state. Required traces: `time`, `ck`, `d`, `dc0`, `dc1`, `dc2`, `dc3`, `dc4`, `dc5`, `dc6`, `vinn`, `vinp`, `vrefn`, `vrefp`.
- `P_ITERATIVE_SEARCH_UPDATES`: exercise and make observable: For each RDAC code, run exactly `iter_num` search-update clocks and halve the step before moving on direction changes. Required traces: `time`, `ck`, `d`, `dc0`, `dc1`, `dc2`, `dc3`, `dc4`, `dc5`, `dc6`, `vinn`, `vinp`, `vrefn`, `vrefp`.
- `P_CODE_UPDATE_AND_RECENTER`: exercise and make observable: The clock after each search window updates the 7-bit code, recenters the search, and advances the sweep without an extra search step. Required traces: `time`, `ck`, `d`, `dc0`, `dc1`, `dc2`, `dc3`, `dc4`, `dc5`, `dc6`, `vinn`, `vinp`, `vrefn`, `vrefp`.

The required trace names are: `time`, `ck`, `d`, `dc0`, `dc1`, `dc2`, `dc3`, `dc4`, `dc5`, `dc6`, `vinn`, `vinp`, `vrefn`, `vrefp`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
