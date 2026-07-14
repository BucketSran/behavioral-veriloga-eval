# PTAT CTAT Reference Generator Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `ptat_ctat_reference_generator.va`:
  - Module `ptat_ctat_reference_generator` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `out` (output, electrical)
    - position 4: `metric` (output, electrical)

## Public Parameter Contract

- `ptat_ctat_reference_generator.tr` defaults to `1e-10` s; valid range: tr > 0; sets output and metric transition smoothing.
- `ptat_ctat_reference_generator.vth` defaults to `0.45` V; valid range: 0 < vth < 0.9; sets clk and rst logic threshold.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_REFERENCE`: restore: Reset initializes out to 0.45 V and metric to 0 V until a valid rising-clock update. Required traces: `time`, `clk`, `rst`, `out`, `metric`.
- `P_INPUT_CLAMP`: restore: Each rising clk update with reset inactive samples vin and clamps the temperature/control value to 0 V through 0.9 V. Required traces: `time`, `clk`, `rst`, `vin`, `out`, `metric`.
- `P_PTAT_TREND`: restore: Metric reports the PTAT branch 0.18 V plus 0.34 times the clamped sampled input and therefore increases monotonically with vin. Required traces: `time`, `clk`, `vin`, `metric`.
- `P_CTAT_PTAT_AVERAGE`: restore: Out is the equal-weight average of PTAT = 0.18 V + 0.34*vin_clamped and CTAT = 0.78 V - 0.34*vin_clamped. Required traces: `time`, `clk`, `vin`, `out`, `metric`.
- `P_REFERENCE_BOUNDS`: restore: Out remains within the public 0 V through 0.9 V voltage range with finite transition smoothing. Required traces: `time`, `out`.

## Modeling Constraints

- Use deterministic sampled voltage-domain behavior.
- Do not use current contributions, transistor-level devices, AC/noise analysis, or KCL/KVL regulation loops.
- Do not add undeclared ports, validation hooks, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `ptat_ctat_reference_generator.va`.
Every supplied `.va` file is editable; do not add or omit files.
