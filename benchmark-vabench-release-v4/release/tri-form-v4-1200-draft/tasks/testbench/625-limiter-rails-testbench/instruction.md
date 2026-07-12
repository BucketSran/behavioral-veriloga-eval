# Limiter Rails Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Limiter Rails` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `limiter_rails.va`:
  - Module `limiter_rails` (entry)
    - position 0: `vdd` (input, electrical)
    - position 1: `vss` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `vmax` (input, electrical)
    - position 4: `vmin` (input, electrical)
    - position 5: `vout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `limiter_rails` as `XDUT` with ordered public binding: vdd=vdd, vss=vss, vin=vin, vmax=vmax, vmin=vmin, vout=vout.

## Public Parameter Contract

- No public parameter is declared.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RAIL_DERIVED_LIMITS`: exercise and make observable: Derive the upper limit as `V(vdd) - V(vmax)` and the lower limit as `V(vss) + V(vmin)`. Required traces: `time`, `vdd`, `vss`, `vin`, `vmax`, `vmin`, `vout`.
- `P_PASS_WITHIN_LIMITS`: exercise and make observable: When `V(vin)` lies between the derived limits, drive `vout` to `V(vin)`. Required traces: `time`, `vin`, `vout`.
- `P_LIMIT_ABOVE_UPPER`: exercise and make observable: When `V(vin)` exceeds the upper limit, drive `vout` to the upper limit. Required traces: `time`, `vdd`, `vin`, `vmax`, `vout`.
- `P_LIMIT_BELOW_LOWER`: exercise and make observable: When `V(vin)` is below the lower limit, drive `vout` to the lower limit. Required traces: `time`, `vss`, `vin`, `vmin`, `vout`.

The required trace names are: `time`, `vdd`, `vin`, `vmax`, `vmin`, `vout`, `vss`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
