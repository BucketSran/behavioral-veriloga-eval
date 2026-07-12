# LNA Blocker Compression Detector Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `lna_blocker_compression_detector.va`:
  - Module `lna_blocker_compression_detector` (entry)
    - position 0: `vin` (inout, electrical)
    - position 1: `blocker` (inout, electrical)
    - position 2: `enable` (inout, electrical)
    - position 3: `rst` (inout, electrical)
    - position 4: `vout` (inout, electrical)
    - position 5: `compression_metric` (inout, electrical)
    - position 6: `compressed` (inout, electrical)

## Public Parameter Contract

- `lna_blocker_compression_detector.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `lna_blocker_compression_detector.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `lna_blocker_compression_detector.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `lna_blocker_compression_detector.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `lna_blocker_compression_detector.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `lna_blocker_compression_detector.small_gain` defaults to `6.0`; valid range: finite; overrides small_gain.
- `lna_blocker_compression_detector.blocker_start` defaults to `0.6`; valid range: finite; overrides blocker_start.
- `lna_blocker_compression_detector.compression_tol` defaults to `0.1`; valid range: finite; overrides compression_tol.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_DISABLED_DRIVE`: restore: On reset or when disabled, drive output to `vcm` and clear compression outputs. Required traces: `time`, `vin`, `blocker`, `enable`, `rst`, `vout`, `compression_metric`, `compressed`.
- `P_AMPLIFY_VIN_VCM_WITH_SMALL_SIGNAL`: restore: Amplify `vin - vcm` with small-signal gain when `blocker` is low. Required traces: `time`, `vin`, `blocker`, `enable`, `rst`, `vout`, `compression_metric`, `compressed`.
- `P_REDUCE_EFFECTIVE_GAIN_AS_BLOCKER_RISES`: restore: Reduce effective gain as `blocker` rises above `blocker_start`. Required traces: `time`, `vin`, `blocker`, `enable`, `rst`, `vout`, `compression_metric`, `compressed`.
- `P_EXPOSE_GAIN_REDUCTION_ON_COMPRESSION_METRIC`: restore: Expose gain reduction on `compression_metric`. Required traces: `time`, `vin`, `blocker`, `enable`, `rst`, `vout`, `compression_metric`, `compressed`.
- `P_ASSERT_COMPRESSED_ONLY_WHEN_THE_EFFECTIVE`: restore: Assert `compressed` only when the effective gain is reduced by more than `compression_tol`. Required traces: `time`, `vin`, `blocker`, `enable`, `rst`, `vout`, `compression_metric`, `compressed`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `lna_blocker_compression_detector.va`.
Every supplied `.va` file is editable; do not add or omit files.
