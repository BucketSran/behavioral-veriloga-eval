# Sample Hold Droop Front End Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `sample_hold_droop_ref.va`:
  - Module `sample_hold_droop_ref` (entry)
    - position 0: `vdd` (inout, electrical)
    - position 1: `vss` (inout, electrical)
    - position 2: `clk` (input, electrical)
    - position 3: `vin` (input, electrical)
    - position 4: `vout` (output, electrical)
    - position 5: `valid` (output, electrical)
    - position 6: `coarse` (output, electrical)

## Public Parameter Contract

- `sample_hold_droop_ref.vth` defaults to `0.45` V; valid range: finite real; sets the clock crossing and coarse-decision threshold.
- `sample_hold_droop_ref.trf` defaults to `4e-11` s; valid range: trf >= 0; sets output transition smoothing.
- `sample_hold_droop_ref.tau` defaults to `9e-08` s; valid range: tau > 0; sets the held-value droop time constant.
- `sample_hold_droop_ref.dt` defaults to `5e-10` s; valid range: dt > 0; sets the interval between bounded droop updates.
- `sample_hold_droop_ref.taperture` defaults to `2e-10` s; valid range: taperture >= 0; sets sampling delay after a rising clk crossing.
- `sample_hold_droop_ref.valid_width` defaults to `2e-09` s; valid range: valid_width > 0; sets the duration of the valid pulse after sampling.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_APERTURE_CAPTURE`: restore: Each rising clk crossing schedules capture of vin after taperture rather than sampling at an unrelated time. Required traces: `time`, `clk`, `vin`, `vout`.
- `P_SUPPLY_CLAMPED_SAMPLE`: restore: At aperture capture, the held output updates to the sampled vin clamped between the instantaneous vss and vdd rails. Required traces: `time`, `vdd`, `vss`, `clk`, `vin`, `vout`.
- `P_COARSE_DECISION`: restore: At each capture, coarse is high when the sampled value exceeds vth and low otherwise, then holds until the next capture. Required traces: `time`, `clk`, `vin`, `coarse`.
- `P_VALID_PULSE`: restore: Valid asserts at the aperture sample and deasserts after valid_width. Required traces: `time`, `clk`, `valid`.
- `P_LOW_PHASE_DROOP`: restore: While clk is low, vout applies bounded droop updates governed by tau and dt instead of remaining ideal or changing discontinuously. Required traces: `time`, `clk`, `vout`.
- `P_NO_TRACK_THROUGH`: restore: Between aperture captures, vout does not transparently track changes on vin; only the specified droop behavior is permitted. Required traces: `time`, `clk`, `vin`, `vout`.

## Modeling Constraints

- Use event-driven delayed sampling, bounded timer-driven droop, and voltage-coded status outputs.
- Use smoothed voltage contributions only.
- Do not use current contributions, ddt(), idt(), validation hooks, testbench-specific timing constants, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `sample_hold_droop_ref.va`.
Every supplied `.va` file is editable; do not add or omit files.
