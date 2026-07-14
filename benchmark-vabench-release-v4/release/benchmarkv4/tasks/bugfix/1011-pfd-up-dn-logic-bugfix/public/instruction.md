# PFD Up DN Logic Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `pfd_updn.va`:
  - Module `pfd_updn` (entry)
    - position 0: `VDD` (inout, electrical)
    - position 1: `VSS` (inout, electrical)
    - position 2: `REF` (input, electrical)
    - position 3: `DIV` (input, electrical)
    - position 4: `UP` (output, electrical)
    - position 5: `DN` (output, electrical)

## Public Parameter Contract

- `pfd_updn.vth` defaults to `0.45` V; valid range: vth > 0; sets REF and DIV rising-edge threshold.
- `pfd_updn.tedge` defaults to `2e-11` s; valid range: tedge > 0; sets UP and DN edge smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_REF_SETS_UP`: restore: A rising REF edge asserts UP, and falling REF edges do not set either output. Required traces: `time`, `ref`, `up`.
- `P_DIV_SETS_DN`: restore: A rising DIV edge asserts DN, and falling DIV edges do not set either output. Required traces: `time`, `div`, `dn`.
- `P_RESET_RACE_CLEAR`: restore: If a rising edge arrives while the opposite output state is already high, both UP and DN clear immediately for REF-leading and DIV-leading orderings. Required traces: `time`, `ref`, `div`, `up`, `dn`.
- `P_NO_PERSISTENT_OVERLAP`: restore: UP and DN are not intentionally held high together beyond finite transition smoothing overlap. Required traces: `time`, `up`, `dn`.
- `P_RAIL_REFERENCE`: restore: UP and DN high levels track the local VDD rail and low levels track the local VSS rail. Required traces: `time`, `vdd`, `vss`, `up`, `dn`.

## Modeling Constraints

- Use deterministic voltage-domain rising-edge behavior for REF and DIV.
- Implement mutual-clear behavior internally; do not add an external reset port.
- Drive UP and DN with voltage contributions and finite smoothing referenced to local VDD/VSS.
- Do not use transistor-level devices, current contributions, ddt(), idt(), validation hooks, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `pfd_updn.va`.
Every supplied `.va` file is editable; do not add or omit files.
