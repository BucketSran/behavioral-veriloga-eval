# Window Comparator Detector Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Window Comparator Detector` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `window_comparator_ref.va`:
  - Module `window_comparator_ref` (entry)
    - position 0: `VDD` (inout, electrical)
    - position 1: `VSS` (inout, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `out` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `window_comparator_ref` as `XDUT` with ordered public binding: VDD=VDD, VSS=VSS, vin=vin, out=out.

## Public Parameter Contract

- `window_comparator_ref.vlow` defaults to `0.3` V; valid range: vlow < vhigh; sets the exclusive lower window threshold relative to VSS.
- `window_comparator_ref.vhigh` defaults to `0.6` V; valid range: vhigh > vlow; sets the exclusive upper window threshold relative to VSS.
- `window_comparator_ref.tedge` defaults to `2e-10` s; valid range: tedge > 0; sets rail-referenced output transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_INITIAL_WINDOW_STATE`: exercise and make observable: At initialization, out reflects whether vin relative to VSS lies strictly between vlow and vhigh. Required traces: `time`, `VSS`, `vin`, `out`.
- `P_INSIDE_WINDOW_HIGH`: exercise and make observable: Out is at the VDD rail only while vlow < V(vin,VSS) < vhigh. Required traces: `time`, `VDD`, `VSS`, `vin`, `out`.
- `P_BOUNDARY_EXCLUSION`: exercise and make observable: Out is at the VSS rail when V(vin,VSS) is equal to or outside either window boundary. Required traces: `time`, `VSS`, `vin`, `out`.
- `P_BIDIRECTIONAL_CROSSINGS`: exercise and make observable: Crossings of both vlow and vhigh in either direction update the retained in-window decision. Required traces: `time`, `vin`, `out`.
- `P_RAIL_SMOOTHING`: exercise and make observable: Out is rail-referenced to VDD and VSS with finite transition smoothing set by tedge. Required traces: `time`, `VDD`, `VSS`, `out`.

The required trace names are: `time`, `VDD`, `VSS`, `vin`, `out`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
