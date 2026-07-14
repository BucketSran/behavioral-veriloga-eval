# Auto-zero Comparator Preamplifier Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `autozero_comparator_preamplifier_top.va`:
  - Module `autozero_comparator_preamplifier_top` (entry)
    - position 0: `vinp` (input, electrical)
    - position 1: `vinn` (input, electrical)
    - position 2: `clk` (input, electrical)
    - position 3: `rst` (input, electrical)
    - position 4: `az_en` (input, electrical)
    - position 5: `eval_en` (input, electrical)
    - position 6: `decision` (output, electrical)
    - position 7: `offset_store` (output, electrical)
    - position 8: `ready` (output, electrical)
- Artifact `offset_store_cell.va`:
  - Module `offset_store_cell` (required_submodule)
    - position 0: `vinp` (input, electrical)
    - position 1: `vinn` (input, electrical)
    - position 2: `clk` (input, electrical)
    - position 3: `rst` (input, electrical)
    - position 4: `az_en` (input, electrical)
    - position 5: `offset_store` (output, electrical)
    - position 6: `ready` (output, electrical)
- Artifact `clocked_comparator_core.va`:
  - Module `clocked_comparator_core` (required_submodule)
    - position 0: `vinp` (input, electrical)
    - position 1: `vinn` (input, electrical)
    - position 2: `clk` (input, electrical)
    - position 3: `rst` (input, electrical)
    - position 4: `eval_en` (input, electrical)
    - position 5: `ready` (input, electrical)
    - position 6: `offset_store` (input, electrical)
    - position 7: `decision` (output, electrical)

## Public Parameter Contract

- `autozero_comparator_preamplifier_top.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `autozero_comparator_preamplifier_top.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `autozero_comparator_preamplifier_top.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `autozero_comparator_preamplifier_top.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `autozero_comparator_preamplifier_top.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `offset_store_cell.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `offset_store_cell.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `offset_store_cell.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `offset_store_cell.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `offset_store_cell.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `clocked_comparator_core.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `clocked_comparator_core.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `clocked_comparator_core.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `clocked_comparator_core.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `clocked_comparator_core.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ON_RESET_CLEAR_STORED_OFFSET_DECISION`: restore: On reset, clear stored offset, `decision`, and `ready`. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `az_en`, `eval_en`, `decision`, `offset_store`, `ready`.
- `P_DURING_AN_AUTO_ZERO_CLOCK_UPDATE`: restore: During an auto-zero clock update with `az_en` high, store the apparent differential offset between `vinp` and `vinn`. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `az_en`, `eval_en`, `decision`, `offset_store`, `ready`.
- `P_DURING_AN_EVALUATION_CLOCK_UPDATE_WITH`: restore: During an evaluation clock update with `eval_en` high, subtract the stored offset from the live differential input. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `az_en`, `eval_en`, `decision`, `offset_store`, `ready`.
- `P_DRIVE_DECISION_HIGH_FOR_CORRECTED_NONNEGATIVE`: restore: Drive `decision` high for corrected nonnegative differential input and low otherwise. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `az_en`, `eval_en`, `decision`, `offset_store`, `ready`.
- `P_EXPOSE_STORED_OFFSET_ON_OFFSET_STORE`: restore: Expose stored offset on `offset_store` and assert `ready` after at least one auto-zero update. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `az_en`, `eval_en`, `decision`, `offset_store`, `ready`.
- `P_USE_ONLY_VOLTAGE_DOMAIN_BEHAVIORAL_STATE`: restore: Use only voltage-domain behavioral state and voltage contributions on public electrical outputs. Required traces: `time`, `vinp`, `vinn`, `clk`, `rst`, `az_en`, `eval_en`, `decision`, `offset_store`, `ready`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `autozero_comparator_preamplifier_top.va`, `offset_store_cell.va`, `clocked_comparator_core.va`.
Every supplied `.va` file is editable; do not add or omit files.
