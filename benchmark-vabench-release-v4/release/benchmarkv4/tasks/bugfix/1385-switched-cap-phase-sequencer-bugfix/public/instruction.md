# Switched-cap Phase Sequencer Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `hold_flagger.va`:
  - Module `hold_flagger` (required_submodule)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `enable` (input, electrical)
    - position 3: `phase_code_1` (input, electrical)
    - position 4: `phase_code_0` (input, electrical)
    - position 5: `valid` (output, electrical)
- Artifact `nonoverlap_phase_gen.va`:
  - Module `nonoverlap_phase_gen` (required_submodule)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `enable` (input, electrical)
    - position 3: `phi1` (output, electrical)
    - position 4: `phi2` (output, electrical)
    - position 5: `phi3` (output, electrical)
    - position 6: `phi4` (output, electrical)
    - position 7: `phase_code_1` (output, electrical)
    - position 8: `phase_code_0` (output, electrical)
- Artifact `sample_switch_scheduler.va`:
  - Module `sample_switch_scheduler` (required_submodule)
    - position 0: `phi1` (input, electrical)
    - position 1: `phi2` (input, electrical)
    - position 2: `phi3` (input, electrical)
    - position 3: `phi4` (input, electrical)
    - position 4: `sample_cmd` (output, electrical)
    - position 5: `hold_cmd` (output, electrical)
- Artifact `switched_cap_phase_seq_top.va`:
  - Module `switched_cap_phase_seq_top` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `enable` (input, electrical)
    - position 3: `phi1` (output, electrical)
    - position 4: `phi2` (output, electrical)
    - position 5: `phi3` (output, electrical)
    - position 6: `phi4` (output, electrical)
    - position 7: `sample_cmd` (output, electrical)
    - position 8: `hold_cmd` (output, electrical)
    - position 9: `phase_code_1` (output, electrical)
    - position 10: `phase_code_0` (output, electrical)
    - position 11: `valid` (output, electrical)

## Public Parameter Contract

- `hold_flagger.vdd` defaults to `0.9` V; valid range: vdd > vss; overrides the public vdd behavior parameter consistently for this module.
- `hold_flagger.vss` defaults to `0` V; valid range: vss < vdd; overrides the public vss behavior parameter consistently for this module.
- `hold_flagger.vth` defaults to `0.45` V; valid range: vth is finite and preserves the public operating range; overrides the public vth behavior parameter consistently for this module.
- `hold_flagger.tr` defaults to `2e-10` s; valid range: tr > 0; overrides the public tr behavior parameter consistently for this module.
- `nonoverlap_phase_gen.vdd` defaults to `0.9` V; valid range: vdd > vss; overrides the public vdd behavior parameter consistently for this module.
- `nonoverlap_phase_gen.vss` defaults to `0` V; valid range: vss < vdd; overrides the public vss behavior parameter consistently for this module.
- `nonoverlap_phase_gen.vth` defaults to `0.45` V; valid range: vth is finite and preserves the public operating range; overrides the public vth behavior parameter consistently for this module.
- `nonoverlap_phase_gen.tr` defaults to `2e-10` s; valid range: tr > 0; overrides the public tr behavior parameter consistently for this module.
- `sample_switch_scheduler.vdd` defaults to `0.9` V; valid range: vdd > vss; overrides the public vdd behavior parameter consistently for this module.
- `sample_switch_scheduler.vss` defaults to `0` V; valid range: vss < vdd; overrides the public vss behavior parameter consistently for this module.
- `sample_switch_scheduler.vth` defaults to `0.45` V; valid range: vth is finite and preserves the public operating range; overrides the public vth behavior parameter consistently for this module.
- `sample_switch_scheduler.tr` defaults to `2e-10` s; valid range: tr > 0; overrides the public tr behavior parameter consistently for this module.
- `switched_cap_phase_seq_top.vdd` defaults to `0.9` V; valid range: vdd > vss; overrides the public vdd behavior parameter consistently for this module.
- `switched_cap_phase_seq_top.vss` defaults to `0` V; valid range: vss < vdd; overrides the public vss behavior parameter consistently for this module.
- `switched_cap_phase_seq_top.vth` defaults to `0.45` V; valid range: vth is finite and preserves the public operating range; overrides the public vth behavior parameter consistently for this module.
- `switched_cap_phase_seq_top.tr` defaults to `2e-10` s; valid range: tr > 0; overrides the public tr behavior parameter consistently for this module.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_DISABLE_CLEAR`: restore: Reset or disabled operation clears all phase outputs, commands, phase code, and valid. Required traces: `time`, `clk`, `rst`, `enable`, `phi1`, `phi2`, `phi3`, `phi4`, `sample_cmd`, `hold_cmd`, `phase_code_1`, `phase_code_0`, `valid`.
- `P_ONE_HOT_SEQUENCE`: restore: Enabled rising clock edges advance cyclically through four one-hot phases with no overlapping high phases. Required traces: `time`, `clk`, `rst`, `enable`, `phi1`, `phi2`, `phi3`, `phi4`.
- `P_COMMAND_MAPPING`: restore: sample_cmd is high exactly for phi1 or phi2, while hold_cmd is high exactly for phi3 or phi4. Required traces: `time`, `phi1`, `phi2`, `phi3`, `phi4`, `sample_cmd`, `hold_cmd`.
- `P_PHASE_CODE`: restore: phase_code_1 and phase_code_0 encode the active phase index zero through three. Required traces: `time`, `phi1`, `phi2`, `phi3`, `phi4`, `phase_code_1`, `phase_code_0`.
- `P_VALID_AFTER_SEQUENCE`: restore: valid remains low initially and asserts only after a complete enabled four-phase sample/hold sequence. Required traces: `time`, `clk`, `rst`, `enable`, `phase_code_1`, `phase_code_0`, `valid`.

## Modeling Constraints

- Use deterministic voltage-domain transient behavior.
- Use portable Spectre-compatible Verilog-A and voltage contributions for public outputs.
- Do not use branch-current oracles, hidden pass/fail ports, checker side channels, or testbench code in the DUT bundle.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `hold_flagger.va`, `nonoverlap_phase_gen.va`, `sample_switch_scheduler.va`, `switched_cap_phase_seq_top.va`.
Every supplied `.va` file is editable; do not add or omit files.
