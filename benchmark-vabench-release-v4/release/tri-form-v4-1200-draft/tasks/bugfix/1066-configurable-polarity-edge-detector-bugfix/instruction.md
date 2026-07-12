# Configurable Polarity Edge Detector Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `configurable_polarity_edge_detector.va`:
  - Module `configurable_polarity_edge_detector` (entry)
    - position 0: `sig` (input, electrical)
    - position 1: `rise_en` (input, electrical)
    - position 2: `pulse` (output, electrical)

## Public Parameter Contract

- `configurable_polarity_edge_detector.vdd` defaults to `0.9` V; valid range: vdd > 0; sets the voltage-coded pulse high level.
- `configurable_polarity_edge_detector.vth` defaults to `0.45` V; valid range: 0 < vth < vdd; sets the decision threshold for sig and rise_en.
- `configurable_polarity_edge_detector.tr` defaults to `2e-11` s; valid range: tr > 0; sets pulse rise and fall smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RISING_SELECTION`: restore: When rise_en is above vth, each rising crossing of sig through vth produces one output pulse. Required traces: `time`, `sig`, `rise_en`, `pulse`.
- `P_FALLING_SELECTION`: restore: When rise_en is below vth, each falling crossing of sig through vth produces one output pulse. Required traces: `time`, `sig`, `rise_en`, `pulse`.
- `P_OPPOSITE_EDGE_REJECTION`: restore: An edge opposite to the polarity selected by rise_en does not produce a pulse. Required traces: `time`, `sig`, `rise_en`, `pulse`.
- `P_BOUNDED_PULSE`: restore: Each detected edge produces a bounded short pulse with nominal width about 2 ns rather than a latched high level. Required traces: `time`, `pulse`.
- `P_OUTPUT_LEVELS`: restore: pulse uses 0 V and vdd levels with finite transition smoothing set by tr. Required traces: `time`, `pulse`.

## Modeling Constraints

- AMS role: selectable-polarity edge qualification block for mixed-signal timing/readout flows.
- Use threshold-crossing events and deterministic bounded pulse state.
- Keep event-triggered state changes separate from continuous output contribution.
- Do not add undeclared ports, artifacts, or validation-only timing hooks.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `configurable_polarity_edge_detector.va`.
Every supplied `.va` file is editable; do not add or omit files.
