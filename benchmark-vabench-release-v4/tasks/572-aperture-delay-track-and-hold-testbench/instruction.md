# Aperture Delay Track And Hold Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Aperture Delay Track And Hold` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `sample_hold_aperture_ref.va`:
  - Module `sample_hold_aperture_ref` (entry)
    - position 0: `VDD` (inout, electrical)
    - position 1: `VSS` (inout, electrical)
    - position 2: `clk` (input, electrical)
    - position 3: `vin` (input, electrical)
    - position 4: `vout` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `sample_hold_aperture_ref` as `XDUT` with ordered public binding: VDD=VDD, VSS=VSS, clk=clk, vin=vin, vout=vout.

## Public Parameter Contract

- `sample_hold_aperture_ref.vth` defaults to `0.45` V; valid range: vth > 0; sets the rising-edge threshold for clk.
- `sample_hold_aperture_ref.taperture` defaults to `2e-10` s; valid range: taperture >= 0; sets the delay from each rising clk crossing to the vin capture instant.
- `sample_hold_aperture_ref.tedge` defaults to `5e-11` s; valid range: tedge > 0; sets vout transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_INITIAL_VALUE`: exercise and make observable: At initialization, the held output is established from the initial observed vin value. Required traces: `time`, `vin`, `vout`.
- `P_APERTURE_ARM`: exercise and make observable: Each rising crossing of clk through vth arms exactly one sample for the corresponding delayed aperture instant. Required traces: `time`, `clk`, `vin`, `vout`.
- `P_DELAYED_CAPTURE`: exercise and make observable: At taperture after the rising clk crossing, vout captures the vin value present at that delayed instant rather than at the clock edge. Required traces: `time`, `clk`, `vin`, `vout`.
- `P_HOLD`: exercise and make observable: Between delayed aperture instants, vout retains the most recently captured value and does not track vin. Required traces: `time`, `clk`, `vin`, `vout`.
- `P_RAIL_OBSERVABILITY`: exercise and make observable: VDD and VSS are public supply-observation ports for harness compatibility only; they do not clamp, scale, or shift the captured vin value. Required traces: `time`, `VDD`, `VSS`, `vin`, `vout`.
- `P_OUTPUT_SMOOTHING`: exercise and make observable: Changes in the held value appear on vout with finite transition smoothing set by tedge. Required traces: `time`, `vin`, `vout`.

The required trace names are: `time`, `VDD`, `VSS`, `clk`, `vin`, `vout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
