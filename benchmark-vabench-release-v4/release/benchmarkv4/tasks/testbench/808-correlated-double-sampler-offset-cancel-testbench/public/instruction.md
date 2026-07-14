# Correlated Double Sampler Offset-cancel Macro Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Correlated Double Sampler Offset-cancel Macro` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `correlated_double_sampler_top` as `XDUT` with ordered public binding: vin=vin, clk=clk, rst=rst, sample_reset=sample_reset, sample_signal=sample_signal, vout=vout, offset_dbg=offset_dbg, valid=valid.

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

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_RESET_CLEAR_RESET_SAMPLE_SIGNAL`: exercise and make observable: On reset, clear reset-sample, signal-sample, output, debug metric, and `valid`. Required traces: `time`, `vin`, `clk`, `rst`, `sample_reset`, `sample_signal`, `vout`, `offset_dbg`, `valid`.
- `P_ON_A_RISING_CLK_EDGE_WITH`: exercise and make observable: On a rising `clk` edge with `sample_reset` high, capture `vin` as the reset/reference sample. Required traces: `time`, `vin`, `clk`, `rst`, `sample_reset`, `sample_signal`, `vout`, `offset_dbg`, `valid`.
- `P_ON_A_LATER_RISING_CLK_EDGE`: exercise and make observable: On a later rising `clk` edge with `sample_signal` high, capture `vin` as the signal sample. Required traces: `time`, `vin`, `clk`, `rst`, `sample_reset`, `sample_signal`, `vout`, `offset_dbg`, `valid`.
- `P_DRIVE_VOUT_AS_VCM_PLUS_THE`: exercise and make observable: Drive `vout` as `vcm` plus the signal-minus-reset difference scaled by `cds_gain`. Required traces: `time`, `vin`, `clk`, `rst`, `sample_reset`, `sample_signal`, `vout`, `offset_dbg`, `valid`.
- `P_EXPOSE_THE_RESET_SAMPLE_ON_OFFSET`: exercise and make observable: Expose the reset sample on `offset_dbg` and assert `valid` only after a complete reset/signal pair. Required traces: `time`, `vin`, `clk`, `rst`, `sample_reset`, `sample_signal`, `vout`, `offset_dbg`, `valid`.
- `P_USE_ONLY_VOLTAGE_DOMAIN_BEHAVIORAL_STATE`: exercise and make observable: Use only voltage-domain behavioral state and voltage contributions on public electrical outputs. Required traces: `time`, `vin`, `clk`, `rst`, `sample_reset`, `sample_signal`, `vout`, `offset_dbg`, `valid`.

The required trace names are: `time`, `vin`, `clk`, `rst`, `sample_reset`, `sample_signal`, `vout`, `offset_dbg`, `valid`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
