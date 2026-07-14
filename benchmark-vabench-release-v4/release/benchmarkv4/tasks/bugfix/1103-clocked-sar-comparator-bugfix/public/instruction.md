# Clocked SAR Comparator Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `clocked_sar_comparator.va`:
  - Module `clocked_sar_comparator` (entry)
    - position 0: `CMPCK` (input, electrical)
    - position 1: `VINN` (input, electrical)
    - position 2: `VINP` (input, electrical)
    - position 3: `DCMPN` (output, electrical)
    - position 4: `DCMPP` (output, electrical)

## Public Parameter Contract

- `clocked_sar_comparator.vdd` defaults to `0.9` V; valid range: vdd > 0; sets the logic-high level and twice the CMPCK crossing threshold.
- `clocked_sar_comparator.td_cmp` defaults to `2e-11` s; valid range: td_cmp >= 0; sets output delay after clock events.
- `clocked_sar_comparator.tr` defaults to `5e-12` s; valid range: tr >= 0; sets decision-output transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_INITIAL_PRECHARGE`: restore: Both decision outputs initialize high at vdd. Required traces: `time`, `dcmpn`, `dcmpp`.
- `P_FALLING_EDGE_PRECHARGE`: restore: Each falling CMPCK crossing through vdd/2 resets both DCMPN and DCMPP high. Required traces: `time`, `cmpck`, `dcmpn`, `dcmpp`.
- `P_POSITIVE_DIFFERENTIAL_DECISION`: restore: On a rising CMPCK crossing with VINP greater than VINN, DCMPP is high and DCMPN is low. Required traces: `time`, `cmpck`, `vinp`, `vinn`, `dcmpn`, `dcmpp`.
- `P_NEGATIVE_DIFFERENTIAL_DECISION`: restore: On a rising CMPCK crossing with VINP less than VINN, DCMPN is high and DCMPP is low. Required traces: `time`, `cmpck`, `vinp`, `vinn`, `dcmpn`, `dcmpp`.
- `P_EQUAL_INPUT_DECISION`: restore: On a rising CMPCK crossing with equal differential inputs, both decision outputs become low. Required traces: `time`, `cmpck`, `vinp`, `vinn`, `dcmpn`, `dcmpp`.
- `P_LATCHED_HOLD_AND_TIMING`: restore: The precharged or decided state holds between clock events and output changes use td_cmp delay and tr smoothing. Required traces: `time`, `cmpck`, `dcmpn`, `dcmpp`.

## Modeling Constraints

- Update decision state only at CMPCK crossings through vdd/2 and hold it between events.
- Drive smooth voltage-coded outputs using td_cmp and tr.
- Do not use current contributions, ddt(), idt(), validation hooks, testbench-specific sample points, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `clocked_sar_comparator.va`.
Every supplied `.va` file is editable; do not add or omit files.
