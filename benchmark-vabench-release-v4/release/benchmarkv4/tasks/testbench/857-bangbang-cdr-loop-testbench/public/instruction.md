# Bang-bang CDR Loop Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Bang-bang CDR Loop` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `cdr_top` as `XDUT` with ordered public binding: data_edge=data_edge, ref_clk=ref_clk, rst=rst, enable=enable, recovered_clk=recovered_clk, early=early, late=late, phase_4=phase_4, phase_3=phase_3, phase_2=phase_2, phase_1=phase_1, phase_0=phase_0, lock=lock.

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

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_DISABLE_CLEAR`: exercise and make observable: Reset or low enable restores phase_center and clears detector, lock, and recovered-clock state. Required traces: `time`, `rst`, `enable`, `recovered_clk`, `early`, `late`, `phase_4`, `phase_3`, `phase_2`, `phase_1`, `phase_0`, `lock`.
- `P_BANGBANG_DECISION`: exercise and make observable: Each data edge is classified against the nearest recovered-clock edge as early, late, or coincident. Required traces: `time`, `data_edge`, `recovered_clk`, `rst`, `enable`, `early`, `late`.
- `P_PHASE_CODE_UPDATE`: exercise and make observable: Late and early decisions move the clamped phase code in opposite declared directions. Required traces: `time`, `data_edge`, `recovered_clk`, `early`, `late`, `phase_4`, `phase_3`, `phase_2`, `phase_1`, `phase_0`.
- `P_PHASE_ROTATION`: exercise and make observable: Recovered-clock edges preserve the reference-clock waveform with phase-code-proportional delay. Required traces: `time`, `ref_clk`, `recovered_clk`, `rst`, `enable`, `phase_4`, `phase_3`, `phase_2`, `phase_1`, `phase_0`.
- `P_LOCK_QUALIFICATION`: exercise and make observable: Lock requires four in-window decisions and drops after two consecutive out-of-window decisions. Required traces: `time`, `data_edge`, `recovered_clk`, `rst`, `enable`, `phase_4`, `phase_3`, `phase_2`, `phase_1`, `phase_0`, `lock`.

The required trace names are: `time`, `data_edge`, `ref_clk`, `rst`, `enable`, `recovered_clk`, `early`, `late`, `phase_4`, `phase_3`, `phase_2`, `phase_1`, `phase_0`, `lock`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
