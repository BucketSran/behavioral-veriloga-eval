# Bang-bang CDR Loop Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `cdr_top.va`:
  - Module `cdr_top` (entry)
    - position 0: `data_edge` (input, electrical)
    - position 1: `ref_clk` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `enable` (input, electrical)
    - position 4: `recovered_clk` (output, electrical)
    - position 5: `early` (output, electrical)
    - position 6: `late` (output, electrical)
    - position 7: `phase_4` (output, electrical)
    - position 8: `phase_3` (output, electrical)
    - position 9: `phase_2` (output, electrical)
    - position 10: `phase_1` (output, electrical)
    - position 11: `phase_0` (output, electrical)
    - position 12: `lock` (output, electrical)
- Artifact `bbpd.va`:
  - Module `bbpd` (required_submodule)
    - position 0: `data_edge` (input, electrical)
    - position 1: `recovered_clk` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `enable` (input, electrical)
    - position 4: `early` (output, electrical)
    - position 5: `late` (output, electrical)
    - position 6: `decision_clk` (output, electrical)
    - position 7: `phase_error` (output, electrical)
- Artifact `loop_filter_code.va`:
  - Module `loop_filter_code` (required_submodule)
    - position 0: `decision_clk` (input, electrical)
    - position 1: `early` (input, electrical)
    - position 2: `late` (input, electrical)
    - position 3: `phase_error` (input, electrical)
    - position 4: `rst` (input, electrical)
    - position 5: `enable` (input, electrical)
    - position 6: `phase_4` (output, electrical)
    - position 7: `phase_3` (output, electrical)
    - position 8: `phase_2` (output, electrical)
    - position 9: `phase_1` (output, electrical)
    - position 10: `phase_0` (output, electrical)
    - position 11: `lock` (output, electrical)
- Artifact `phase_rotator.va`:
  - Module `phase_rotator` (required_submodule)
    - position 0: `ref_clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `enable` (input, electrical)
    - position 3: `phase_4` (input, electrical)
    - position 4: `phase_3` (input, electrical)
    - position 5: `phase_2` (input, electrical)
    - position 6: `phase_1` (input, electrical)
    - position 7: `phase_0` (input, electrical)
    - position 8: `recovered_clk` (output, electrical)

## Public Parameter Contract

- `cdr_top.vdd` defaults to `0.9`; valid range: finite; overrides vdd for module cdr_top.
- `cdr_top.vss` defaults to `0.0`; valid range: finite; overrides vss for module cdr_top.
- `cdr_top.vth` defaults to `0.45`; valid range: finite; overrides vth for module cdr_top.
- `cdr_top.phase_center` defaults to `16`; valid range: integer; overrides phase_center for module cdr_top.
- `cdr_top.unit_phase_delay` defaults to `5e-12`; valid range: finite; overrides unit_phase_delay for module cdr_top.
- `cdr_top.lock_window` defaults to `2`; valid range: integer; overrides lock_window for module cdr_top.
- `cdr_top.tr` defaults to `200p`; valid range: finite; overrides tr for module cdr_top.
- `bbpd.vdd` defaults to `0.9`; valid range: finite; overrides vdd for module bbpd.
- `bbpd.vss` defaults to `0.0`; valid range: finite; overrides vss for module bbpd.
- `bbpd.vth` defaults to `0.45`; valid range: finite; overrides vth for module bbpd.
- `bbpd.unit_phase_delay` defaults to `5e-12`; valid range: finite; overrides unit_phase_delay for module bbpd.
- `bbpd.tr` defaults to `200p`; valid range: finite; overrides tr for module bbpd.
- `loop_filter_code.vdd` defaults to `0.9`; valid range: finite; overrides vdd for module loop_filter_code.
- `loop_filter_code.vss` defaults to `0.0`; valid range: finite; overrides vss for module loop_filter_code.
- `loop_filter_code.vth` defaults to `0.45`; valid range: finite; overrides vth for module loop_filter_code.
- `loop_filter_code.phase_center` defaults to `16`; valid range: integer; overrides phase_center for module loop_filter_code.
- `loop_filter_code.lock_window` defaults to `2`; valid range: integer; overrides lock_window for module loop_filter_code.
- `loop_filter_code.tr` defaults to `200p`; valid range: finite; overrides tr for module loop_filter_code.
- `phase_rotator.vdd` defaults to `0.9`; valid range: finite; overrides vdd for module phase_rotator.
- `phase_rotator.vss` defaults to `0.0`; valid range: finite; overrides vss for module phase_rotator.
- `phase_rotator.vth` defaults to `0.45`; valid range: finite; overrides vth for module phase_rotator.
- `phase_rotator.unit_phase_delay` defaults to `5e-12`; valid range: finite; overrides unit_phase_delay for module phase_rotator.
- `phase_rotator.tr` defaults to `200p`; valid range: finite; overrides tr for module phase_rotator.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_DISABLE_CLEAR`: restore: Reset or low enable restores phase_center and clears detector, lock, and recovered-clock state. Required traces: `time`, `rst`, `enable`, `recovered_clk`, `early`, `late`, `phase_4`, `phase_3`, `phase_2`, `phase_1`, `phase_0`, `lock`.
- `P_BANGBANG_DECISION`: restore: Each data edge is classified against the nearest recovered-clock edge as early, late, or coincident. Required traces: `time`, `data_edge`, `recovered_clk`, `rst`, `enable`, `early`, `late`.
- `P_PHASE_CODE_UPDATE`: restore: Late and early decisions move the clamped phase code in opposite declared directions. Required traces: `time`, `data_edge`, `recovered_clk`, `early`, `late`, `phase_4`, `phase_3`, `phase_2`, `phase_1`, `phase_0`.
- `P_PHASE_ROTATION`: restore: Recovered-clock edges preserve the reference-clock waveform with phase-code-proportional delay. Required traces: `time`, `ref_clk`, `recovered_clk`, `rst`, `enable`, `phase_4`, `phase_3`, `phase_2`, `phase_1`, `phase_0`.
- `P_LOCK_QUALIFICATION`: restore: Lock requires four in-window decisions and drops after two consecutive out-of-window decisions. Required traces: `time`, `data_edge`, `recovered_clk`, `rst`, `enable`, `phase_4`, `phase_3`, `phase_2`, `phase_1`, `phase_0`, `lock`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Preserve the declared module graph, port order, parameter override behavior, and public trace observability.
- Do not hard-code evaluator stimulus, stop times, sample windows, checker tolerances, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `cdr_top.va`, `bbpd.va`, `loop_filter_code.va`, `phase_rotator.va`.
Every supplied `.va` file is editable; do not add or omit files.
