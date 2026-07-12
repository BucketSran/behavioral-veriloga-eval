# Polynomial Differential VCVS Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `polynomial_differential_vcvs.va`:
  - Module `polynomial_differential_vcvs` (entry)
    - position 0: `inp` (input, electrical)
    - position 1: `inn` (input, electrical)
    - position 2: `outp` (output, electrical)
    - position 3: `outn` (output, electrical)

## Public Parameter Contract

- `polynomial_differential_vcvs.vcmo` defaults to `1.1`; valid range: finite; overrides vcmo.
- `polynomial_differential_vcvs.a1` defaults to `1`; valid range: finite; overrides a1.
- `polynomial_differential_vcvs.a2` defaults to `0`; valid range: finite; overrides a2.
- `polynomial_differential_vcvs.a3` defaults to `0`; valid range: finite; overrides a3.
- `polynomial_differential_vcvs.a5` defaults to `0`; valid range: finite; overrides a5.
- `polynomial_differential_vcvs.a7` defaults to `0`; valid range: finite; overrides a7.
- `polynomial_differential_vcvs.vsat` defaults to `10000000`; valid range: finite; overrides vsat.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_POLYNOMIAL_DIFFERENTIAL_INPUT`: restore: Compute the polynomial from `vid = V(inp, inn)` using coefficients `a1`, `a2`, `a3`, `a5`, and `a7` through seventh order. Required traces: `time`, `inp`, `inn`, `outp`, `outn`.
- `P_HALF_SWING_SPLIT`: restore: Divide the polynomial result by two and drive `outp = vcmo + limited_vod`, `outn = vcmo - limited_vod`. Required traces: `time`, `inp`, `inn`, `outp`, `outn`.
- `P_SYMMETRIC_SATURATION`: restore: Limit the half-swing to the inclusive interval `[-vsat, vsat]` before driving both outputs. Required traces: `time`, `inp`, `inn`, `outp`, `outn`.
- `P_OUTPUT_COMMON_MODE`: restore: Keep both outputs symmetric around the common-mode parameter `vcmo`. Required traces: `time`, `outp`, `outn`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `polynomial_differential_vcvs.va`.
Every supplied `.va` file is editable; do not add or omit files.
