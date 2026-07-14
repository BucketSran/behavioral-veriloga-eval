# Power and Reset Sequencer Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `power_reset_seq_top.va`:
  - Module `power_reset_seq_top` (entry)
    - position 0: `vdd_sense` (input, electrical)
    - position 1: `clk` (input, electrical)
    - position 2: `rst_n_ext` (input, electrical)
    - position 3: `enable_req` (input, electrical)
    - position 4: `por_n` (output, electrical)
    - position 5: `rst_n_core` (output, electrical)
    - position 6: `en_ana` (output, electrical)
    - position 7: `en_dig` (output, electrical)
    - position 8: `ready` (output, electrical)
- Artifact `por_detector.va`:
  - Module `por_detector` (required_submodule)
    - position 0: `vdd_sense` (input, electrical)
    - position 1: `clk` (input, electrical)
    - position 2: `rst_n_ext` (input, electrical)
    - position 3: `por_n` (output, electrical)
- Artifact `reset_synchronizer.va`:
  - Module `reset_synchronizer` (required_submodule)
    - position 0: `clk` (input, electrical)
    - position 1: `por_n` (input, electrical)
    - position 2: `enable_req` (input, electrical)
    - position 3: `rst_n_core` (output, electrical)
- Artifact `enable_sequencer.va`:
  - Module `enable_sequencer` (required_submodule)
    - position 0: `clk` (input, electrical)
    - position 1: `rst_n_core` (input, electrical)
    - position 2: `en_ana` (output, electrical)
    - position 3: `en_dig` (output, electrical)
- Artifact `ready_flag.va`:
  - Module `ready_flag` (required_submodule)
    - position 0: `clk` (input, electrical)
    - position 1: `en_ana` (input, electrical)
    - position 2: `en_dig` (input, electrical)
    - position 3: `ready` (output, electrical)

## Public Parameter Contract

- `power_reset_seq_top.vhi` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vhi for this module.
- `power_reset_seq_top.vlo` defaults to `0.0` V; valid range: finite and consistent with the declared rail domain; overrides vlo for this module.
- `power_reset_seq_top.vpor` defaults to `0.72` V; valid range: finite and consistent with the declared rail domain; overrides vpor for this module.
- `power_reset_seq_top.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `power_reset_seq_top.tr` defaults to `200e-12` s; valid range: tr > 0; overrides tr for this module.
- `por_detector.vhi` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vhi for this module.
- `por_detector.vlo` defaults to `0.0` V; valid range: finite and consistent with the declared rail domain; overrides vlo for this module.
- `por_detector.vpor` defaults to `0.72` V; valid range: finite and consistent with the declared rail domain; overrides vpor for this module.
- `por_detector.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `por_detector.tr` defaults to `200e-12` s; valid range: tr > 0; overrides tr for this module.
- `reset_synchronizer.vhi` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vhi for this module.
- `reset_synchronizer.vlo` defaults to `0.0` V; valid range: finite and consistent with the declared rail domain; overrides vlo for this module.
- `reset_synchronizer.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `reset_synchronizer.tr` defaults to `200e-12` s; valid range: tr > 0; overrides tr for this module.
- `enable_sequencer.vhi` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vhi for this module.
- `enable_sequencer.vlo` defaults to `0.0` V; valid range: finite and consistent with the declared rail domain; overrides vlo for this module.
- `enable_sequencer.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `enable_sequencer.tr` defaults to `200e-12` s; valid range: tr > 0; overrides tr for this module.
- `ready_flag.vhi` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vhi for this module.
- `ready_flag.vlo` defaults to `0.0` V; valid range: finite and consistent with the declared rail domain; overrides vlo for this module.
- `ready_flag.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `ready_flag.tr` defaults to `200e-12` s; valid range: tr > 0; overrides tr for this module.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_PWR_ASYNC_CLEAR`: restore: External reset or a brownout clears por_n, core reset release, enables, and ready without waiting for sequence completion. Required traces: `time`, `vdd_sense`, `rst_n_ext`, `por_n`, `rst_n_core`, `en_ana`, `en_dig`, `ready`.
- `P_PWR_POR_DEBOUNCE`: restore: por_n asserts only after two consecutive good-power rising clock edges. Required traces: `time`, `vdd_sense`, `clk`, `rst_n_ext`, `por_n`.
- `P_PWR_SEQUENCE_ORDER`: restore: With power good and enable requested, rst_n_core, en_ana, and en_dig release on successive rising clock edges. Required traces: `time`, `vdd_sense`, `clk`, `rst_n_ext`, `enable_req`, `por_n`, `rst_n_core`, `en_ana`, `en_dig`.
- `P_PWR_READY_DELAY`: restore: ready asserts one rising clock after both enables are high. Required traces: `time`, `clk`, `en_ana`, `en_dig`, `ready`.

## Modeling Constraints

- Use deterministic voltage-domain transient behavioral Verilog-A.
- Preserve the declared multi-module architecture and exact public artifact interfaces.
- Do not use current contributions, unsupported continuous operators, validation logic, hard-coded evaluator timing, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `power_reset_seq_top.va`, `por_detector.va`, `reset_synchronizer.va`, `enable_sequencer.va`, `ready_flag.va`.
Every supplied `.va` file is editable; do not add or omit files.
