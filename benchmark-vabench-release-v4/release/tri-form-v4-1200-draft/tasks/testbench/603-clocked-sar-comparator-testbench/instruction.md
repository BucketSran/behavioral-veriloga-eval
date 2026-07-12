# Clocked SAR Comparator Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Clocked SAR Comparator` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `clocked_sar_comparator.va`:
  - Module `clocked_sar_comparator` (entry)
    - position 0: `CMPCK` (input, electrical)
    - position 1: `VINN` (input, electrical)
    - position 2: `VINP` (input, electrical)
    - position 3: `DCMPN` (output, electrical)
    - position 4: `DCMPP` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `clocked_sar_comparator` as `XDUT` with ordered public binding: CMPCK=cmpck, VINN=vinn, VINP=vinp, DCMPN=dcmpn, DCMPP=dcmpp.

## Public Parameter Contract

- `clocked_sar_comparator.vdd` defaults to `0.9` V; valid range: vdd > 0; sets the logic-high level and twice the CMPCK crossing threshold.
- `clocked_sar_comparator.td_cmp` defaults to `2e-11` s; valid range: td_cmp >= 0; sets output delay after clock events.
- `clocked_sar_comparator.tr` defaults to `5e-12` s; valid range: tr >= 0; sets decision-output transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_INITIAL_PRECHARGE`: exercise and make observable: Both decision outputs initialize high at vdd. Required traces: `time`, `dcmpn`, `dcmpp`.
- `P_FALLING_EDGE_PRECHARGE`: exercise and make observable: Each falling CMPCK crossing through vdd/2 resets both DCMPN and DCMPP high. Required traces: `time`, `cmpck`, `dcmpn`, `dcmpp`.
- `P_POSITIVE_DIFFERENTIAL_DECISION`: exercise and make observable: On a rising CMPCK crossing with VINP greater than VINN, DCMPP is high and DCMPN is low. Required traces: `time`, `cmpck`, `vinp`, `vinn`, `dcmpn`, `dcmpp`.
- `P_NEGATIVE_DIFFERENTIAL_DECISION`: exercise and make observable: On a rising CMPCK crossing with VINP less than VINN, DCMPN is high and DCMPP is low. Required traces: `time`, `cmpck`, `vinp`, `vinn`, `dcmpn`, `dcmpp`.
- `P_EQUAL_INPUT_DECISION`: exercise and make observable: On a rising CMPCK crossing with equal differential inputs, both decision outputs become low. Required traces: `time`, `cmpck`, `vinp`, `vinn`, `dcmpn`, `dcmpp`.
- `P_LATCHED_HOLD_AND_TIMING`: exercise and make observable: The precharged or decided state holds between clock events and output changes use td_cmp delay and tr smoothing. Required traces: `time`, `cmpck`, `dcmpn`, `dcmpp`.

The required trace names are: `time`, `cmpck`, `vinn`, `vinp`, `dcmpn`, `dcmpp`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
