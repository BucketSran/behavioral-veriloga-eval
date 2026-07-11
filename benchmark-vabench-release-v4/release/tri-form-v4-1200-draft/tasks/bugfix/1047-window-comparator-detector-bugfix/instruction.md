# Window Comparator Detector Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `window_comparator_ref.va`:
  - Module `window_comparator_ref` (entry)
    - position 0: `VDD` (inout, electrical)
    - position 1: `VSS` (inout, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `out` (output, electrical)

## Public Parameter Contract

- `window_comparator_ref.vlow` defaults to `0.3` V; valid range: vlow < vhigh; sets the exclusive lower window threshold relative to VSS.
- `window_comparator_ref.vhigh` defaults to `0.6` V; valid range: vhigh > vlow; sets the exclusive upper window threshold relative to VSS.
- `window_comparator_ref.tedge` defaults to `2e-10` s; valid range: tedge > 0; sets rail-referenced output transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_INITIAL_WINDOW_STATE`: restore: At initialization, out reflects whether vin relative to VSS lies strictly between vlow and vhigh. Required traces: `time`, `VSS`, `vin`, `out`.
- `P_INSIDE_WINDOW_HIGH`: restore: Out is at the VDD rail only while vlow < V(vin,VSS) < vhigh. Required traces: `time`, `VDD`, `VSS`, `vin`, `out`.
- `P_BOUNDARY_EXCLUSION`: restore: Out is at the VSS rail when V(vin,VSS) is equal to or outside either window boundary. Required traces: `time`, `VSS`, `vin`, `out`.
- `P_BIDIRECTIONAL_CROSSINGS`: restore: Crossings of both vlow and vhigh in either direction update the retained in-window decision. Required traces: `time`, `vin`, `out`.
- `P_RAIL_SMOOTHING`: restore: Out is rail-referenced to VDD and VSS with finite transition smoothing set by tedge. Required traces: `time`, `VDD`, `VSS`, `out`.

## Modeling Constraints

- Use deterministic threshold-crossing state updates and voltage contributions only.
- Drive the output contribution outside crossing event blocks.
- Do not use current contributions, ddt(), idt(), validation hooks, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `window_comparator_ref.va`.
Every supplied `.va` file is editable; do not add or omit files.
