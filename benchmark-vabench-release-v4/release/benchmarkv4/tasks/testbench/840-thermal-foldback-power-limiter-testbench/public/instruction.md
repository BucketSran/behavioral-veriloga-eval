# Thermal Foldback Power Limiter Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Thermal Foldback Power Limiter` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `thermal_foldback_power_limiter_top.va`:
  - Module `thermal_foldback_power_limiter_top` (entry)
    - position 0: `power_cmd` (inout, electrical)
    - position 1: `temp_sense` (inout, electrical)
    - position 2: `clk` (inout, electrical)
    - position 3: `rst` (inout, electrical)
    - position 4: `enable` (inout, electrical)
    - position 5: `limited_cmd` (inout, electrical)
    - position 6: `foldback_metric` (inout, electrical)
    - position 7: `thermal_ok` (inout, electrical)
- Artifact `foldback_controller.va`:
  - Module `foldback_controller` (required_submodule)
    - position 0: `temp_sense` (inout, electrical)
    - position 1: `clk` (inout, electrical)
    - position 2: `rst` (inout, electrical)
    - position 3: `enable` (inout, electrical)
    - position 4: `foldback_factor` (inout, electrical)
    - position 5: `foldback_metric` (inout, electrical)
    - position 6: `thermal_ok` (inout, electrical)
- Artifact `command_limiter.va`:
  - Module `command_limiter` (required_submodule)
    - position 0: `power_cmd` (inout, electrical)
    - position 1: `rst` (inout, electrical)
    - position 2: `enable` (inout, electrical)
    - position 3: `foldback_factor` (inout, electrical)
    - position 4: `limited_cmd` (inout, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `thermal_foldback_power_limiter_top` as `XDUT` with ordered public binding: power_cmd=power_cmd, temp_sense=temp_sense, clk=clk, rst=rst, enable=enable, limited_cmd=limited_cmd, foldback_metric=foldback_metric, thermal_ok=thermal_ok.

## Public Parameter Contract

- `thermal_foldback_power_limiter_top.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `thermal_foldback_power_limiter_top.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `thermal_foldback_power_limiter_top.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `thermal_foldback_power_limiter_top.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `thermal_foldback_power_limiter_top.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `thermal_foldback_power_limiter_top.temp_trip` defaults to `0.65`; valid range: finite; overrides temp_trip.
- `foldback_controller.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `foldback_controller.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `foldback_controller.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `foldback_controller.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `foldback_controller.temp_trip` defaults to `0.65`; valid range: finite; overrides temp_trip.
- `foldback_controller.temp_full` defaults to `0.85`; valid range: finite; overrides temp_full.
- `command_limiter.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `command_limiter.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `command_limiter.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `command_limiter.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_RESET_OR_WHEN_DISABLED_CLEAR`: exercise and make observable: On reset or when disabled, clear limited command, foldback metric, and status. Required traces: `time`, `power_cmd`, `temp_sense`, `clk`, `rst`, `enable`, `limited_cmd`, `foldback_metric`, `thermal_ok`.
- `P_ON_EACH_ENABLED_RISING_CLK_EDGE`: exercise and make observable: On each enabled rising `clk` edge, compare `temp_sense` against the foldback threshold. Required traces: `time`, `power_cmd`, `temp_sense`, `clk`, `rst`, `enable`, `limited_cmd`, `foldback_metric`, `thermal_ok`.
- `P_PASS_POWER_CMD_THROUGH_WHILE_TEMPERATURE`: exercise and make observable: Pass `power_cmd` through while temperature is below threshold. Required traces: `time`, `power_cmd`, `temp_sense`, `clk`, `rst`, `enable`, `limited_cmd`, `foldback_metric`, `thermal_ok`.
- `P_REDUCE_LIMITED_CMD_AS_TEMPERATURE_RISES`: exercise and make observable: Reduce `limited_cmd` as temperature rises above threshold and expose the reduction on `foldback_metric`. Required traces: `time`, `power_cmd`, `temp_sense`, `clk`, `rst`, `enable`, `limited_cmd`, `foldback_metric`, `thermal_ok`.
- `P_ASSERT_THERMAL_OK_ONLY_WHEN_NO`: exercise and make observable: Assert `thermal_ok` only when no foldback reduction is active. Required traces: `time`, `power_cmd`, `temp_sense`, `clk`, `rst`, `enable`, `limited_cmd`, `foldback_metric`, `thermal_ok`.

The required trace names are: `time`, `power_cmd`, `temp_sense`, `clk`, `rst`, `enable`, `limited_cmd`, `foldback_metric`, `thermal_ok`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
