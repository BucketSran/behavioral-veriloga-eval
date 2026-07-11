# Pipeline ADC Stage Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `pipeline_stage.va`:
  - Module `pipeline_stage` (entry)
    - position 0: `VDD` (input, electrical)
    - position 1: `VSS` (input, electrical)
    - position 2: `PHI1` (input, electrical)
    - position 3: `PHI2` (input, electrical)
    - position 4: `VIN` (input, electrical)
    - position 5: `VREF` (input, electrical)
    - position 6: `VRES` (output, electrical)
    - position 7: `D1` (output, electrical)
    - position 8: `D0` (output, electrical)

## Public Parameter Contract

- `pipeline_stage.vth` defaults to `0.45` V; valid range: V(VSS) < vth < V(VDD); sets PHI1 and PHI2 decision threshold.
- `pipeline_stage.vdd` defaults to `0.9` V; valid range: vdd > 0; sets nominal initialized output high level.
- `pipeline_stage.tedge` defaults to `2e-10` s; valid range: tedge > 0; sets output transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_TWO_PHASE_SAMPLING`: restore: VIN is sampled on a rising PHI1 edge and converted on a rising PHI2 edge. Required traces: `time`, `PHI1`, `PHI2`, `VIN`, `VRES`, `D1`, `D0`.
- `P_SUBADC_REGIONS`: restore: Upper, middle, and lower sampled-input regions produce decision codes 10, 01, and 00 respectively. Required traces: `time`, `PHI2`, `VIN`, `VREF`, `D1`, `D0`.
- `P_RESIDUE_MAPPING`: restore: The residue is gain-two with the specified half-reference subtraction, no offset, or addition for the three regions. Required traces: `time`, `PHI2`, `VIN`, `VREF`, `VRES`, `D1`, `D0`.
- `P_RESIDUE_CLAMP`: restore: VRES remains within the VSS-to-VDD supply range. Required traces: `time`, `VDD`, `VSS`, `VRES`.

## Modeling Constraints

- Use deterministic voltage-domain behavior.
- Do not use current contributions, ddt(), idt(), validation logic, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `pipeline_stage.va`.
Every supplied `.va` file is editable; do not add or omit files.
