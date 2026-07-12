# Switched-cap Phase Sequencer Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Switched-cap Phase Sequencer` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `switched_cap_phase_seq_top` as `XDUT` with ordered public binding: clk=clk, rst=rst, enable=enable, phi1=phi1, phi2=phi2, phi3=phi3, phi4=phi4, sample_cmd=sample_cmd, hold_cmd=hold_cmd, phase_code_1=phase_code_1, phase_code_0=phase_code_0, valid=valid.

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

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_DISABLE_CLEAR`: exercise and make observable: Reset or disabled operation clears all phase outputs, commands, phase code, and valid. Required traces: `time`, `clk`, `rst`, `enable`, `phi1`, `phi2`, `phi3`, `phi4`, `sample_cmd`, `hold_cmd`, `phase_code_1`, `phase_code_0`, `valid`.
- `P_ONE_HOT_SEQUENCE`: exercise and make observable: Enabled rising clock edges advance cyclically through four one-hot phases with no overlapping high phases. Required traces: `time`, `clk`, `rst`, `enable`, `phi1`, `phi2`, `phi3`, `phi4`.
- `P_COMMAND_MAPPING`: exercise and make observable: sample_cmd is high exactly for phi1 or phi2, while hold_cmd is high exactly for phi3 or phi4. Required traces: `time`, `phi1`, `phi2`, `phi3`, `phi4`, `sample_cmd`, `hold_cmd`.
- `P_PHASE_CODE`: exercise and make observable: phase_code_1 and phase_code_0 encode the active phase index zero through three. Required traces: `time`, `phi1`, `phi2`, `phi3`, `phi4`, `phase_code_1`, `phase_code_0`.
- `P_VALID_AFTER_SEQUENCE`: exercise and make observable: valid remains low initially and asserts only after a complete enabled four-phase sample/hold sequence. Required traces: `time`, `clk`, `rst`, `enable`, `phase_code_1`, `phase_code_0`, `valid`.

The required trace names are: `time`, `clk`, `rst`, `enable`, `phi1`, `phi2`, `phi3`, `phi4`, `sample_cmd`, `hold_cmd`, `phase_code_1`, `phase_code_0`, `valid`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
