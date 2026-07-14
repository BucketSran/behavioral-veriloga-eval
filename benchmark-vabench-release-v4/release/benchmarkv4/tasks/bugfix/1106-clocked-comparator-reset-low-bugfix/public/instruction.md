# Clocked Comparator Reset Low Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `clocked_comparator_reset_low.va`:
  - Module `clocked_comparator_reset_low` (entry)
    - position 0: `CMPCK` (input, electrical)
    - position 1: `VINN` (input, electrical)
    - position 2: `VINP` (input, electrical)
    - position 3: `DCMPN` (output, electrical)
    - position 4: `DCMPP` (output, electrical)

## Public Parameter Contract

- `clocked_comparator_reset_low.vdd` defaults to `0.9` V; valid range: vdd > 0; sets logic-high level and twice the CMPCK decision threshold.
- `clocked_comparator_reset_low.td_cmp` defaults to `1e-10` s; valid range: td_cmp >= 0; sets output decision delay.
- `clocked_comparator_reset_low.tr` defaults to `1e-11` s; valid range: tr >= 0; sets output transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_INITIAL_RESET_LOW`: restore: Both decision outputs initialize low. Required traces: `time`, `dcmpn`, `dcmpp`.
- `P_FALLING_EDGE_RESET_LOW`: restore: Each falling CMPCK crossing through vdd/2 resets both DCMPN and DCMPP low. Required traces: `time`, `cmpck`, `dcmpn`, `dcmpp`.
- `P_POSITIVE_DIFFERENTIAL_DECISION`: restore: On a rising CMPCK crossing with VINP greater than VINN, DCMPP is high and DCMPN is low. Required traces: `time`, `cmpck`, `vinp`, `vinn`, `dcmpn`, `dcmpp`.
- `P_NEGATIVE_DIFFERENTIAL_DECISION`: restore: On a rising CMPCK crossing with VINP less than VINN, DCMPN is high and DCMPP is low. Required traces: `time`, `cmpck`, `vinp`, `vinn`, `dcmpn`, `dcmpp`.
- `P_EQUAL_INPUT_RESET_STATE`: restore: On a rising CMPCK crossing with equal inputs, both outputs remain low. Required traces: `time`, `cmpck`, `vinp`, `vinn`, `dcmpn`, `dcmpp`.
- `P_LATCHED_HOLD_AND_TIMING`: restore: The reset or decided state holds between CMPCK events and output changes use td_cmp delay and tr smoothing. Required traces: `time`, `cmpck`, `dcmpn`, `dcmpp`.

## Modeling Constraints

- Update decision state only at CMPCK crossings through vdd/2 and hold it between events.
- Drive smooth voltage-coded outputs using td_cmp and tr.
- Do not use current contributions, ddt(), idt(), validation hooks, hard-coded waveform sample points, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `clocked_comparator_reset_low.va`.
Every supplied `.va` file is editable; do not add or omit files.
