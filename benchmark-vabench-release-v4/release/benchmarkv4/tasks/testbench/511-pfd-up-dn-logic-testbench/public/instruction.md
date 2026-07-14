# PFD Up DN Logic Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `PFD Up DN Logic` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `pfd_updn.va`:
  - Module `pfd_updn` (entry)
    - position 0: `VDD` (inout, electrical)
    - position 1: `VSS` (inout, electrical)
    - position 2: `REF` (input, electrical)
    - position 3: `DIV` (input, electrical)
    - position 4: `UP` (output, electrical)
    - position 5: `DN` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `pfd_updn` as `XDUT` with ordered public binding: VDD=vdd, VSS=vss, REF=ref, DIV=div, UP=up, DN=dn.

## Public Parameter Contract

- `pfd_updn.vth` defaults to `0.45` V; valid range: vth > 0; sets REF and DIV rising-edge threshold.
- `pfd_updn.tedge` defaults to `2e-11` s; valid range: tedge > 0; sets UP and DN edge smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_REF_SETS_UP`: exercise and make observable: A rising REF edge asserts UP, and falling REF edges do not set either output. Required traces: `time`, `ref`, `up`.
- `P_DIV_SETS_DN`: exercise and make observable: A rising DIV edge asserts DN, and falling DIV edges do not set either output. Required traces: `time`, `div`, `dn`.
- `P_RESET_RACE_CLEAR`: exercise and make observable: If a rising edge arrives while the opposite output state is already high, both UP and DN clear immediately for REF-leading and DIV-leading orderings. Required traces: `time`, `ref`, `div`, `up`, `dn`.
- `P_NO_PERSISTENT_OVERLAP`: exercise and make observable: UP and DN are not intentionally held high together beyond finite transition smoothing overlap. Required traces: `time`, `up`, `dn`.
- `P_RAIL_REFERENCE`: exercise and make observable: UP and DN high levels track the local VDD rail and low levels track the local VSS rail. Required traces: `time`, `vdd`, `vss`, `up`, `dn`.

The required trace names are: `time`, `vdd`, `vss`, `ref`, `div`, `up`, `dn`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
