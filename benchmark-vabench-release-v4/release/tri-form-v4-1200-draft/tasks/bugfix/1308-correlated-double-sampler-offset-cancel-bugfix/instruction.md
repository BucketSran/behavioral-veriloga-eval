# Correlated Double Sampler Offset-cancel Macro Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `correlated_double_sampler_top.va`:
  - Module `correlated_double_sampler_top` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `clk` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `sample_reset` (input, electrical)
    - position 4: `sample_signal` (input, electrical)
    - position 5: `vout` (output, electrical)
    - position 6: `offset_dbg` (output, electrical)
    - position 7: `valid` (output, electrical)
- Artifact `reset_sample_latch.va`:
  - Module `reset_sample_latch` (required_submodule)
    - position 0: `vin` (input, electrical)
    - position 1: `clk` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `sample_reset` (input, electrical)
    - position 4: `reset_node` (output, electrical)
- Artifact `signal_sample_latch.va`:
  - Module `signal_sample_latch` (required_submodule)
    - position 0: `vin` (input, electrical)
    - position 1: `clk` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `sample_signal` (input, electrical)
    - position 4: `reset_node` (input, electrical)
    - position 5: `vout` (output, electrical)
    - position 6: `offset_dbg` (output, electrical)
    - position 7: `valid` (output, electrical)

## Public Parameter Contract

- `correlated_double_sampler_top.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `correlated_double_sampler_top.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `correlated_double_sampler_top.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `correlated_double_sampler_top.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `correlated_double_sampler_top.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `correlated_double_sampler_top.cds_gain` defaults to `1.0`; valid range: finite; overrides cds_gain.
- `reset_sample_latch.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `reset_sample_latch.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `reset_sample_latch.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `reset_sample_latch.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `reset_sample_latch.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `signal_sample_latch.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `signal_sample_latch.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `signal_sample_latch.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `signal_sample_latch.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `signal_sample_latch.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `signal_sample_latch.cds_gain` defaults to `1.0`; valid range: finite; overrides cds_gain.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_CLEAR_RESET_SAMPLE_SIGNAL`: restore: On reset, clear reset-sample, signal-sample, output, debug metric, and `valid`. Required traces: `time`, `vin`, `clk`, `rst`, `sample_reset`, `sample_signal`, `vout`, `offset_dbg`, `valid`.
- `P_ON_A_RISING_CLK_EDGE_WITH`: restore: On a rising `clk` edge with `sample_reset` high, capture `vin` as the reset/reference sample. Required traces: `time`, `vin`, `clk`, `rst`, `sample_reset`, `sample_signal`, `vout`, `offset_dbg`, `valid`.
- `P_ON_A_LATER_RISING_CLK_EDGE`: restore: On a later rising `clk` edge with `sample_signal` high, capture `vin` as the signal sample. Required traces: `time`, `vin`, `clk`, `rst`, `sample_reset`, `sample_signal`, `vout`, `offset_dbg`, `valid`.
- `P_DRIVE_VOUT_AS_VCM_PLUS_THE`: restore: Drive `vout` as `vcm` plus the signal-minus-reset difference scaled by `cds_gain`. Required traces: `time`, `vin`, `clk`, `rst`, `sample_reset`, `sample_signal`, `vout`, `offset_dbg`, `valid`.
- `P_EXPOSE_THE_RESET_SAMPLE_ON_OFFSET`: restore: Expose the reset sample on `offset_dbg` and assert `valid` only after a complete reset/signal pair. Required traces: `time`, `vin`, `clk`, `rst`, `sample_reset`, `sample_signal`, `vout`, `offset_dbg`, `valid`.
- `P_USE_ONLY_VOLTAGE_DOMAIN_BEHAVIORAL_STATE`: restore: Use only voltage-domain behavioral state and voltage contributions on public electrical outputs. Required traces: `time`, `vin`, `clk`, `rst`, `sample_reset`, `sample_signal`, `vout`, `offset_dbg`, `valid`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `correlated_double_sampler_top.va`, `reset_sample_latch.va`, `signal_sample_latch.va`.
Every supplied `.va` file is editable; do not add or omit files.
