# 3-tap FFE Transmitter Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `3-tap FFE Transmitter` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `ffe_tx_3tap` as `XDUT` with ordered public binding: data=data, clk=clk, rst=rst, pre_1=pre_1, pre_0=pre_0, post_1=post_1, post_0=post_0, vout=vout, main_dbg=main_dbg, pre_dbg=pre_dbg, post_dbg=post_dbg.

## Public Parameter Contract

- `ffe_tx_3tap.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `ffe_tx_3tap.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `ffe_tx_3tap.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `ffe_tx_3tap.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `ffe_tx_3tap.main_amp` defaults to `0.18`; valid range: finite; overrides main_amp.
- `ffe_tx_3tap.tap_step` defaults to `0.04`; valid range: finite; overrides tap_step.
- `ffe_tx_3tap.tr` defaults to `120p from (0:inf)`; valid range: finite; overrides tr.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_CLEARS_SYMBOL_HISTORY_AND_DRIVES`: exercise and make observable: Reset clears symbol history and drives all outputs to common mode. Required traces: `time`, `data`, `clk`, `rst`, `pre_1`, `pre_0`, `post_1`, `post_0`, `vout`, `main_dbg`, `pre_dbg`, `post_dbg`.
- `P_ON_EACH_RISING_CLK_SAMPLE_DATA`: exercise and make observable: On each rising `clk`, sample `data` as +1 for high and -1 for low. Required traces: `time`, `data`, `clk`, `rst`, `pre_1`, `pre_0`, `post_1`, `post_0`, `vout`, `main_dbg`, `pre_dbg`, `post_dbg`.
- `P_DRIVE_MAIN_DBG_PRE_DBG_AND`: exercise and make observable: Drive `main_dbg`, `pre_dbg`, and `post_dbg` as voltage-coded per-tap contributions around common mode. Required traces: `time`, `data`, `clk`, `rst`, `pre_1`, `pre_0`, `post_1`, `post_0`, `vout`, `main_dbg`, `pre_dbg`, `post_dbg`.
- `P_VOUT_IS_THE_CLIPPED_SUM_OF`: exercise and make observable: `vout` is the clipped sum of the current main contribution, previous-symbol pre contribution, and older-symbol post contribution. Required traces: `time`, `data`, `clk`, `rst`, `pre_1`, `pre_0`, `post_1`, `post_0`, `vout`, `main_dbg`, `pre_dbg`, `post_dbg`.
- `P_HIGHER_TAP_CONTROL_CODES_MUST_INCREASE`: exercise and make observable: Higher tap-control codes must increase the corresponding contribution magnitude. Required traces: `time`, `data`, `clk`, `rst`, `pre_1`, `pre_0`, `post_1`, `post_0`, `vout`, `main_dbg`, `pre_dbg`, `post_dbg`.

The required trace names are: `time`, `data`, `clk`, `rst`, `pre_1`, `pre_0`, `post_1`, `post_0`, `vout`, `main_dbg`, `pre_dbg`, `post_dbg`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
