# 3-tap FFE Transmitter Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `ffe_tx_3tap.va`:
  - Module `ffe_tx_3tap` (entry)
    - position 0: `data` (input, electrical)
    - position 1: `clk` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `pre_1` (input, electrical)
    - position 4: `pre_0` (input, electrical)
    - position 5: `post_1` (input, electrical)
    - position 6: `post_0` (input, electrical)
    - position 7: `vout` (output, electrical)
    - position 8: `main_dbg` (output, electrical)
    - position 9: `pre_dbg` (output, electrical)
    - position 10: `post_dbg` (output, electrical)

## Public Parameter Contract

- `ffe_tx_3tap.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `ffe_tx_3tap.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `ffe_tx_3tap.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `ffe_tx_3tap.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `ffe_tx_3tap.main_amp` defaults to `0.18`; valid range: finite; overrides main_amp.
- `ffe_tx_3tap.tap_step` defaults to `0.04`; valid range: finite; overrides tap_step.
- `ffe_tx_3tap.tr` defaults to `120p from (0:inf)`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_CLEARS_SYMBOL_HISTORY_AND_DRIVES`: restore: Reset clears symbol history and drives all outputs to common mode. Required traces: `time`, `data`, `clk`, `rst`, `pre_1`, `pre_0`, `post_1`, `post_0`, `vout`, `main_dbg`, `pre_dbg`, `post_dbg`.
- `P_ON_EACH_RISING_CLK_SAMPLE_DATA`: restore: On each rising `clk`, sample `data` as +1 for high and -1 for low. Required traces: `time`, `data`, `clk`, `rst`, `pre_1`, `pre_0`, `post_1`, `post_0`, `vout`, `main_dbg`, `pre_dbg`, `post_dbg`.
- `P_DRIVE_MAIN_DBG_PRE_DBG_AND`: restore: Drive `main_dbg`, `pre_dbg`, and `post_dbg` as voltage-coded per-tap contributions around common mode. Required traces: `time`, `data`, `clk`, `rst`, `pre_1`, `pre_0`, `post_1`, `post_0`, `vout`, `main_dbg`, `pre_dbg`, `post_dbg`.
- `P_VOUT_IS_THE_CLIPPED_SUM_OF`: restore: `vout` is the clipped sum of the current main contribution, previous-symbol pre contribution, and older-symbol post contribution. Required traces: `time`, `data`, `clk`, `rst`, `pre_1`, `pre_0`, `post_1`, `post_0`, `vout`, `main_dbg`, `pre_dbg`, `post_dbg`.
- `P_HIGHER_TAP_CONTROL_CODES_MUST_INCREASE`: restore: Higher tap-control codes must increase the corresponding contribution magnitude. Required traces: `time`, `data`, `clk`, `rst`, `pre_1`, `pre_0`, `post_1`, `post_0`, `vout`, `main_dbg`, `pre_dbg`, `post_dbg`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `ffe_tx_3tap.va`.
Every supplied `.va` file is editable; do not add or omit files.
