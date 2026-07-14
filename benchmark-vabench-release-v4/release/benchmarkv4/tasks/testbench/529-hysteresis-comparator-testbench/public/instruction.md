# Hysteresis Comparator Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Hysteresis Comparator` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `cmp_hysteresis.va`:
  - Module `cmp_hysteresis` (entry)
    - position 0: `VINN` (input, electrical)
    - position 1: `VINP` (input, electrical)
    - position 2: `OUTN` (output, electrical)
    - position 3: `OUTP` (output, electrical)
    - position 4: `VSS` (input, electrical)
    - position 5: `VDD` (input, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `cmp_hysteresis` as `XDUT` with ordered public binding: VINN=vinn, VINP=vinp, OUTN=out_n, OUTP=out_p, VSS=vss, VDD=vdd.

## Public Parameter Contract

- `cmp_hysteresis.vhys` defaults to `0.01` V; valid range: vhys >= 0; sets total differential hysteresis width centered at zero.
- `cmp_hysteresis.tedge` defaults to `5e-11` s; valid range: tedge > 0; sets complementary output transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_INITIAL_DECISION`: exercise and make observable: OUTP initializes high only when the initial differential exceeds positive vhys over two; otherwise OUTP initializes low and OUTN high. Required traces: `time`, `vinp`, `vinn`, `out_p`, `out_n`.
- `P_POSITIVE_SWITCH_THRESHOLD`: exercise and make observable: The low OUTP state switches high only on a rising differential crossing of positive vhys over two. Required traces: `time`, `vinp`, `vinn`, `out_p`, `out_n`.
- `P_NEGATIVE_SWITCH_THRESHOLD`: exercise and make observable: The high OUTP state switches low only on a falling differential crossing of negative vhys over two. Required traces: `time`, `vinp`, `vinn`, `out_p`, `out_n`.
- `P_HYSTERESIS_HOLD`: exercise and make observable: The previous decision is retained while the differential remains inside the hysteresis band. Required traces: `time`, `vinp`, `vinn`, `out_p`, `out_n`.
- `P_COMPLEMENTARY_RAIL_OUTPUT`: exercise and make observable: OUTP and OUTN remain complementary and use the local VDD and VSS rail levels after smoothing. Required traces: `time`, `out_p`, `out_n`, `vdd`, `vss`.

The required trace names are: `time`, `vinn`, `vinp`, `out_n`, `out_p`, `vss`, `vdd`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
