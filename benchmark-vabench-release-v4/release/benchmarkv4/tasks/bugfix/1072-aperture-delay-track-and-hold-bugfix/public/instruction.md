# Aperture Delay Track And Hold Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `sample_hold_aperture_ref.va`:
  - Module `sample_hold_aperture_ref` (entry)
    - position 0: `VDD` (inout, electrical)
    - position 1: `VSS` (inout, electrical)
    - position 2: `clk` (input, electrical)
    - position 3: `vin` (input, electrical)
    - position 4: `vout` (output, electrical)

## Public Parameter Contract

- `sample_hold_aperture_ref.vth` defaults to `0.45` V; valid range: vth > 0; sets the rising-edge threshold for clk.
- `sample_hold_aperture_ref.taperture` defaults to `2e-10` s; valid range: taperture >= 0; sets the delay from each rising clk crossing to the vin capture instant.
- `sample_hold_aperture_ref.tedge` defaults to `5e-11` s; valid range: tedge > 0; sets vout transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_INITIAL_VALUE`: restore: At initialization, the held output is established from the initial observed vin value. Required traces: `time`, `vin`, `vout`.
- `P_APERTURE_ARM`: restore: Each rising crossing of clk through vth arms exactly one sample for the corresponding delayed aperture instant. Required traces: `time`, `clk`, `vin`, `vout`.
- `P_DELAYED_CAPTURE`: restore: At taperture after the rising clk crossing, vout captures the vin value present at that delayed instant rather than at the clock edge. Required traces: `time`, `clk`, `vin`, `vout`.
- `P_HOLD`: restore: Between delayed aperture instants, vout retains the most recently captured value and does not track vin. Required traces: `time`, `clk`, `vin`, `vout`.
- `P_RAIL_OBSERVABILITY`: restore: VDD and VSS are public supply-observation ports for harness compatibility only; they do not clamp, scale, or shift the captured vin value. Required traces: `time`, `VDD`, `VSS`, `vin`, `vout`.
- `P_OUTPUT_SMOOTHING`: restore: Changes in the held value appear on vout with finite transition smoothing set by tedge. Required traces: `time`, `vin`, `vout`.

## Modeling Constraints

- Use deterministic rising-edge arming and delayed event-driven capture.
- Keep held state updates separate from the continuous vout contribution.
- Treat VDD and VSS as observable supply context only; do not clamp, scale, or shift the held vin value with those rails.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `sample_hold_aperture_ref.va`.
Every supplied `.va` file is editable; do not add or omit files.
