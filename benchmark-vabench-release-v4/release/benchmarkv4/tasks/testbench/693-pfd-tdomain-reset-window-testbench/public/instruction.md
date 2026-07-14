# PFD Tdomain Reset Window Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `PFD Tdomain Reset Window` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `pfd_tdomain_reset_window.va`:
  - Module `pfd_tdomain_reset_window` (entry)
    - position 0: `in1` (input, electrical)
    - position 1: `in2` (input, electrical)
    - position 2: `up` (output, electrical)
    - position 3: `dn` (output, electrical)
    - position 4: `vdd` (input, electrical)
    - position 5: `gnd` (input, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `pfd_tdomain_reset_window` as `XDUT` with ordered public binding: in1=in1, in2=in2, up=up, dn=dn, vdd=vdd, gnd=gnd.

## Public Parameter Contract

- `pfd_tdomain_reset_window.ttol` defaults to `5f`; valid range: finite; overrides ttol.
- `pfd_tdomain_reset_window.td` defaults to `0`; valid range: finite; overrides td.
- `pfd_tdomain_reset_window.tt` defaults to `10p`; valid range: finite; overrides tt.
- `pfd_tdomain_reset_window.ton` defaults to `120p`; valid range: finite; overrides ton.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_LEADING_EDGE_DIRECTION`: exercise and make observable: A leading `in1` edge asserts `up`, and a leading `in2` edge asserts `dn`. Required traces: `time`, `dn`, `in1`, `in2`, `up`, `vdd`, `gnd`.
- `P_RESET_OVERLAP_WINDOW`: exercise and make observable: After both inputs arrive, both outputs remain asserted for the `ton` reset-overlap window. Required traces: `time`, `dn`, `in1`, `in2`, `up`, `vdd`, `gnd`.
- `P_CLEAR_AFTER_RESET_WINDOW`: exercise and make observable: After the reset-overlap window, both `up` and `dn` clear before the next phase event. Required traces: `time`, `dn`, `in1`, `in2`, `up`, `vdd`, `gnd`.
- `P_PFD_OUTPUT_LEVELS`: exercise and make observable: `up` and `dn` use rail-referenced voltage-coded low/high levels. Required traces: `time`, `dn`, `in1`, `in2`, `up`, `vdd`, `gnd`.

The required trace names are: `time`, `dn`, `in1`, `in2`, `up`, `vdd`, `gnd`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
