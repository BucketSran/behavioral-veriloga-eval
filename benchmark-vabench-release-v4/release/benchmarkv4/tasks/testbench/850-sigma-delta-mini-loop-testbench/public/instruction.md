# Sigma-delta Modulator Mini Loop Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Sigma-delta Modulator Mini Loop` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `sigma_delta_top.va`:
  - Module `sigma_delta_top` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `clk` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `bit_out` (output, electrical)
    - position 4: `avg_3` (output, electrical)
    - position 5: `avg_2` (output, electrical)
    - position 6: `avg_1` (output, electrical)
    - position 7: `avg_0` (output, electrical)
    - position 8: `state_metric` (output, electrical)
- Artifact `integrator_state.va`:
  - Module `integrator_state` (required_submodule)
    - position 0: `vin` (input, electrical)
    - position 1: `feedback` (input, electrical)
    - position 2: `clk` (input, electrical)
    - position 3: `rst` (input, electrical)
    - position 4: `state_metric` (output, electrical)
- Artifact `sd_comparator.va`:
  - Module `sd_comparator` (required_submodule)
    - position 0: `state_metric` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `bit_out` (output, electrical)
- Artifact `feedback_dac.va`:
  - Module `feedback_dac` (required_submodule)
    - position 0: `bit_in` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `feedback` (output, electrical)
- Artifact `decimator_lite.va`:
  - Module `decimator_lite` (required_submodule)
    - position 0: `bit_in` (input, electrical)
    - position 1: `clk` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `avg_3` (output, electrical)
    - position 4: `avg_2` (output, electrical)
    - position 5: `avg_1` (output, electrical)
    - position 6: `avg_0` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `sigma_delta_top` as `XDUT` with ordered public binding: vin=vin, clk=clk, rst=rst, bit_out=bit_out, avg_3=avg_3, avg_2=avg_2, avg_1=avg_1, avg_0=avg_0, state_metric=state_metric.

## Public Parameter Contract

- `sigma_delta_top.vdd` defaults to `0.9`; valid range: finite; overrides vdd for module sigma_delta_top.
- `sigma_delta_top.vss` defaults to `0.0`; valid range: finite; overrides vss for module sigma_delta_top.
- `sigma_delta_top.vcm` defaults to `0.45`; valid range: finite; overrides vcm for module sigma_delta_top.
- `sigma_delta_top.vth` defaults to `0.45`; valid range: finite; overrides vth for module sigma_delta_top.
- `sigma_delta_top.state_limit` defaults to `1.8`; valid range: finite; overrides state_limit for module sigma_delta_top.
- `sigma_delta_top.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr for module sigma_delta_top.
- `integrator_state.vcm` defaults to `0.45`; valid range: finite; overrides vcm for module integrator_state.
- `integrator_state.vth` defaults to `0.45`; valid range: finite; overrides vth for module integrator_state.
- `integrator_state.state_limit` defaults to `1.8`; valid range: finite; overrides state_limit for module integrator_state.
- `integrator_state.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr for module integrator_state.
- `sd_comparator.vdd` defaults to `0.9`; valid range: finite; overrides vdd for module sd_comparator.
- `sd_comparator.vss` defaults to `0.0`; valid range: finite; overrides vss for module sd_comparator.
- `sd_comparator.vcm` defaults to `0.45`; valid range: finite; overrides vcm for module sd_comparator.
- `sd_comparator.vth` defaults to `0.45`; valid range: finite; overrides vth for module sd_comparator.
- `sd_comparator.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr for module sd_comparator.
- `feedback_dac.vdd` defaults to `0.9`; valid range: finite; overrides vdd for module feedback_dac.
- `feedback_dac.vss` defaults to `0.0`; valid range: finite; overrides vss for module feedback_dac.
- `feedback_dac.vth` defaults to `0.45`; valid range: finite; overrides vth for module feedback_dac.
- `feedback_dac.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr for module feedback_dac.
- `decimator_lite.vdd` defaults to `0.9`; valid range: finite; overrides vdd for module decimator_lite.
- `decimator_lite.vss` defaults to `0.0`; valid range: finite; overrides vss for module decimator_lite.
- `decimator_lite.vth` defaults to `0.45`; valid range: finite; overrides vth for module decimator_lite.
- `decimator_lite.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr for module decimator_lite.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_CLEAR`: exercise and make observable: Reset clears the loop state, output bit, and decimator result. Required traces: `time`, `rst`, `bit_out`, `avg_3`, `avg_2`, `avg_1`, `avg_0`, `state_metric`.
- `P_FEEDBACK_STATE_UPDATE`: exercise and make observable: Each rising clock edge updates the bounded integrator from VIN and the previous feedback bit. Required traces: `time`, `vin`, `clk`, `rst`, `bit_out`, `state_metric`.
- `P_COMPARATOR_DECISION`: exercise and make observable: The output bit reflects the updated state relative to VCM. Required traces: `time`, `clk`, `rst`, `bit_out`, `state_metric`.
- `P_DECIMATOR_WINDOW`: exercise and make observable: The four-bit result reports the saturated high-bit count for each complete 16-sample window. Required traces: `time`, `clk`, `rst`, `bit_out`, `avg_3`, `avg_2`, `avg_1`, `avg_0`.
- `P_STATE_BOUNDED`: exercise and make observable: The public state metric remains within the configured state limit. Required traces: `time`, `rst`, `state_metric`.

The required trace names are: `time`, `vin`, `clk`, `rst`, `bit_out`, `avg_3`, `avg_2`, `avg_1`, `avg_0`, `state_metric`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
