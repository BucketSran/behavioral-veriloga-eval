# Common-mode Feedback Loop Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Common-mode Feedback Loop` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `cmfb_loop_top.va`:
  - Module `cmfb_loop_top` (entry)
    - position 0: `vop_in` (input, electrical)
    - position 1: `von_in` (input, electrical)
    - position 2: `clk` (input, electrical)
    - position 3: `rst` (input, electrical)
    - position 4: `enable` (input, electrical)
    - position 5: `vop_out` (output, electrical)
    - position 6: `von_out` (output, electrical)
    - position 7: `trim_2` (output, electrical)
    - position 8: `trim_1` (output, electrical)
    - position 9: `trim_0` (output, electrical)
    - position 10: `cm_error` (output, electrical)
    - position 11: `locked` (output, electrical)
- Artifact `cm_sensor.va`:
  - Module `cm_sensor` (required_submodule)
    - position 0: `vop_in` (input, electrical)
    - position 1: `von_in` (input, electrical)
    - position 2: `cm_error_raw` (output, electrical)
- Artifact `trim_controller.va`:
  - Module `trim_controller` (required_submodule)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `enable` (input, electrical)
    - position 3: `cm_error_raw` (input, electrical)
    - position 4: `trim_2` (output, electrical)
    - position 5: `trim_1` (output, electrical)
    - position 6: `trim_0` (output, electrical)
    - position 7: `trim_corr` (output, electrical)
    - position 8: `locked` (output, electrical)
- Artifact `output_balancer.va`:
  - Module `output_balancer` (required_submodule)
    - position 0: `vop_in` (input, electrical)
    - position 1: `von_in` (input, electrical)
    - position 2: `enable` (input, electrical)
    - position 3: `rst` (input, electrical)
    - position 4: `trim_corr` (input, electrical)
    - position 5: `vop_out` (output, electrical)
    - position 6: `von_out` (output, electrical)
    - position 7: `cm_error` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `cmfb_loop_top` as `XDUT` with ordered public binding: vop_in=vop_in, von_in=von_in, clk=clk, rst=rst, enable=enable, vop_out=vop_out, von_out=von_out, trim_2=trim_2, trim_1=trim_1, trim_0=trim_0, cm_error=cm_error, locked=locked.

## Public Parameter Contract

- `cmfb_loop_top.vdd` defaults to `0.9` V; valid range: vdd > vss; sets the logic-high output level.
- `cmfb_loop_top.vss` defaults to `0.0` V; valid range: vss < vdd; sets the logic-low output level.
- `cmfb_loop_top.vcm` defaults to `0.45` V; valid range: vss < vcm < vdd; sets the target common mode.
- `cmfb_loop_top.vth` defaults to `0.45` V; valid range: vss < vth < vdd; sets the digital-voltage crossing threshold.
- `cmfb_loop_top.trim_lsb` defaults to `0.01` V; valid range: trim_lsb > 0; sets one unsigned trim correction step.
- `cmfb_loop_top.lock_tol` defaults to `0.01` V; valid range: lock_tol >= 0; sets the residual-error lock tolerance.
- `cmfb_loop_top.tr` defaults to `2e-10` s; valid range: tr > 0; sets output transition smoothing.
- `cm_sensor.vcm` defaults to `0.45` V; valid range: finite; sets target common mode.
- `cm_sensor.tr` defaults to `2e-10` s; valid range: tr > 0; sets transition smoothing.
- `trim_controller.vdd` defaults to `0.9` V; valid range: vdd > vss; sets the logic-high output level.
- `trim_controller.vss` defaults to `0.0` V; valid range: vss < vdd; sets the logic-low output level.
- `trim_controller.vth` defaults to `0.45` V; valid range: vss < vth < vdd; sets the digital-voltage crossing threshold.
- `trim_controller.trim_lsb` defaults to `0.01` V; valid range: trim_lsb > 0; sets one correction step.
- `trim_controller.lock_tol` defaults to `0.01` V; valid range: lock_tol >= 0; sets lock tolerance.
- `trim_controller.tr` defaults to `2e-10` s; valid range: tr > 0; sets transition smoothing.
- `output_balancer.vdd` defaults to `0.9` V; valid range: vdd > vss; sets the logic-high output level.
- `output_balancer.vss` defaults to `0.0` V; valid range: vss < vdd; sets the logic-low output level.
- `output_balancer.vcm` defaults to `0.45` V; valid range: vss < vcm < vdd; sets target common mode.
- `output_balancer.vth` defaults to `0.45` V; valid range: vss < vth < vdd; sets the digital-voltage crossing threshold.
- `output_balancer.tr` defaults to `2e-10` s; valid range: tr > 0; sets transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_DISABLE_CLEAR`: exercise and make observable: Reset or disable clears trim and lock, reports zero residual error, and bypasses correction. Required traces: `time`, `vop_in`, `von_in`, `clk`, `rst`, `enable`, `vop_out`, `von_out`, `trim_2`, `trim_1`, `trim_0`, `cm_error`, `locked`.
- `P_COMMON_MODE_ERROR`: exercise and make observable: The reported common-mode error equals the corrected output average minus vcm. Required traces: `time`, `vop_in`, `von_in`, `clk`, `rst`, `enable`, `vop_out`, `von_out`, `trim_2`, `trim_1`, `trim_0`, `cm_error`, `locked`.
- `P_TRIM_DIRECTION`: exercise and make observable: At enabled rising clock edges the bounded unsigned trim code moves in the direction that reduces representable positive common-mode error. Required traces: `time`, `vop_in`, `von_in`, `clk`, `rst`, `enable`, `vop_out`, `von_out`, `trim_2`, `trim_1`, `trim_0`, `cm_error`, `locked`.
- `P_DIFFERENTIAL_PRESERVATION`: exercise and make observable: Common-mode correction preserves input differential polarity and differential magnitude unless a supply clamp is reached. Required traces: `time`, `vop_in`, `von_in`, `clk`, `rst`, `enable`, `vop_out`, `von_out`, `trim_2`, `trim_1`, `trim_0`, `cm_error`, `locked`.
- `P_LOCK_QUALIFICATION`: exercise and make observable: Lock asserts only after two consecutive enabled updates within lock_tol. Required traces: `time`, `vop_in`, `von_in`, `clk`, `rst`, `enable`, `vop_out`, `von_out`, `trim_2`, `trim_1`, `trim_0`, `cm_error`, `locked`.

The required trace names are: `time`, `vop_in`, `von_in`, `clk`, `rst`, `enable`, `vop_out`, `von_out`, `trim_2`, `trim_1`, `trim_0`, `cm_error`, `locked`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
