# Polynomial Differential VCVS Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Polynomial Differential VCVS` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `polynomial_differential_vcvs.va`:
  - Module `polynomial_differential_vcvs` (entry)
    - position 0: `inp` (input, electrical)
    - position 1: `inn` (input, electrical)
    - position 2: `outp` (output, electrical)
    - position 3: `outn` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `polynomial_differential_vcvs` as `XDUT` with ordered public binding: inp=inp, inn=inn, outp=outp, outn=outn.

## Public Parameter Contract

- `polynomial_differential_vcvs.vcmo` defaults to `1.1`; valid range: finite; overrides vcmo.
- `polynomial_differential_vcvs.a1` defaults to `1`; valid range: finite; overrides a1.
- `polynomial_differential_vcvs.a2` defaults to `0`; valid range: finite; overrides a2.
- `polynomial_differential_vcvs.a3` defaults to `0`; valid range: finite; overrides a3.
- `polynomial_differential_vcvs.a5` defaults to `0`; valid range: finite; overrides a5.
- `polynomial_differential_vcvs.a7` defaults to `0`; valid range: finite; overrides a7.
- `polynomial_differential_vcvs.vsat` defaults to `10000000`; valid range: finite; overrides vsat.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_POLYNOMIAL_DIFFERENTIAL_INPUT`: exercise and make observable: Compute the polynomial from `vid = V(inp, inn)` using coefficients `a1`, `a2`, `a3`, `a5`, and `a7` through seventh order. Required traces: `time`, `inp`, `inn`, `outp`, `outn`.
- `P_HALF_SWING_SPLIT`: exercise and make observable: Divide the polynomial result by two and drive `outp = vcmo + limited_vod`, `outn = vcmo - limited_vod`. Required traces: `time`, `inp`, `inn`, `outp`, `outn`.
- `P_SYMMETRIC_SATURATION`: exercise and make observable: Limit the half-swing to the inclusive interval `[-vsat, vsat]` before driving both outputs. Required traces: `time`, `inp`, `inn`, `outp`, `outn`.
- `P_OUTPUT_COMMON_MODE`: exercise and make observable: Keep both outputs symmetric around the common-mode parameter `vcmo`. Required traces: `time`, `outp`, `outn`.

The required trace names are: `time`, `inn`, `inp`, `outn`, `outp`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
