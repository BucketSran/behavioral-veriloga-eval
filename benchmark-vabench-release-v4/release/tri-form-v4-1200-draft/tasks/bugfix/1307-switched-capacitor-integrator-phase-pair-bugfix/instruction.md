# Switched-capacitor Integrator Phase Pair Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `switched_cap_integrator_phase_pair_top.va`:
  - Module `switched_cap_integrator_phase_pair_top` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `phi1` (input, electrical)
    - position 2: `phi2` (input, electrical)
    - position 3: `rst` (input, electrical)
    - position 4: `enable` (input, electrical)
    - position 5: `vout` (output, electrical)
    - position 6: `phase_metric` (output, electrical)
    - position 7: `valid` (output, electrical)
- Artifact `sample_phase_cell.va`:
  - Module `sample_phase_cell` (required_submodule)
    - position 0: `vin` (input, electrical)
    - position 1: `phi1` (input, electrical)
    - position 2: `phi2` (input, electrical)
    - position 3: `rst` (input, electrical)
    - position 4: `enable` (input, electrical)
    - position 5: `sample_node` (output, electrical)
    - position 6: `sample_valid` (output, electrical)
- Artifact `integrator_state_cell.va`:
  - Module `integrator_state_cell` (required_submodule)
    - position 0: `phi1` (input, electrical)
    - position 1: `phi2` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `enable` (input, electrical)
    - position 4: `sample_node` (input, electrical)
    - position 5: `sample_valid` (input, electrical)
    - position 6: `vout` (output, electrical)
    - position 7: `phase_metric` (output, electrical)
    - position 8: `valid` (output, electrical)

## Public Parameter Contract

- `switched_cap_integrator_phase_pair_top.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `switched_cap_integrator_phase_pair_top.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `switched_cap_integrator_phase_pair_top.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `switched_cap_integrator_phase_pair_top.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `switched_cap_integrator_phase_pair_top.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `switched_cap_integrator_phase_pair_top.k_int` defaults to `0.2`; valid range: finite; overrides k_int.
- `sample_phase_cell.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `sample_phase_cell.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `sample_phase_cell.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `sample_phase_cell.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `sample_phase_cell.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `integrator_state_cell.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `integrator_state_cell.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `integrator_state_cell.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `integrator_state_cell.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `integrator_state_cell.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `integrator_state_cell.k_int` defaults to `0.2`; valid range: finite; overrides k_int.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_OR_WHEN_DISABLED_CLEAR`: restore: On reset or when disabled, clear the integration state, drive `vout` to `vcm`, and clear `valid`. Required traces: `time`, `vin`, `phi1`, `phi2`, `rst`, `enable`, `vout`, `phase_metric`, `valid`.
- `P_ON_A_RISING_PHI1_CROSSING_SAMPLE`: restore: On a rising `phi1` crossing, sample the input deviation from `vcm` into the sampling state. Required traces: `time`, `vin`, `phi1`, `phi2`, `rst`, `enable`, `vout`, `phase_metric`, `valid`.
- `P_ON_THE_FOLLOWING_RISING_PHI2_CROSSING`: restore: On the following rising `phi2` crossing, add `k_int` times the sampled deviation to the integrator state. Required traces: `time`, `vin`, `phi1`, `phi2`, `rst`, `enable`, `vout`, `phase_metric`, `valid`.
- `P_REJECT_OVERLAPPING_PHI1_AND_PHI2_UPDATES`: restore: Reject overlapping `phi1` and `phi2` updates by holding the previous state and lowering `valid` for that cycle. Required traces: `time`, `vin`, `phi1`, `phi2`, `rst`, `enable`, `vout`, `phase_metric`, `valid`.
- `P_EXPOSE_THE_MOST_RECENT_ACCEPTED_PHASE`: restore: Expose the most recent accepted phase pair on `phase_metric` and clamp `vout` to the rails. Required traces: `time`, `vin`, `phi1`, `phi2`, `rst`, `enable`, `vout`, `phase_metric`, `valid`.
- `P_USE_ONLY_VOLTAGE_DOMAIN_BEHAVIORAL_STATE`: restore: Use only voltage-domain behavioral state and voltage contributions on public electrical outputs. Required traces: `time`, `vin`, `phi1`, `phi2`, `rst`, `enable`, `vout`, `phase_metric`, `valid`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `switched_cap_integrator_phase_pair_top.va`, `sample_phase_cell.va`, `integrator_state_cell.va`.
Every supplied `.va` file is editable; do not add or omit files.
