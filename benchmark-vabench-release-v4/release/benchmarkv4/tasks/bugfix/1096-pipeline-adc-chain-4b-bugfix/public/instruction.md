# Pipeline ADC Chain 4b Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `pipeline_adc_chain_4b.va`:
  - Module `pipeline_adc_chain_4b` (entry)
    - position 0: `VDD` (inout, electrical)
    - position 1: `VSS` (inout, electrical)
    - position 2: `VIN` (input, electrical)
    - position 3: `CLK` (input, electrical)
    - position 4: `RES1` (output, electrical)
    - position 5: `RES2` (output, electrical)
    - position 6: `S1B1` (output, electrical)
    - position 7: `S1B0` (output, electrical)
    - position 8: `S2B1` (output, electrical)
    - position 9: `S2B0` (output, electrical)
    - position 10: `DOUT3` (output, electrical)
    - position 11: `DOUT2` (output, electrical)
    - position 12: `DOUT1` (output, electrical)
    - position 13: `DOUT0` (output, electrical)

## Public Parameter Contract

- `pipeline_adc_chain_4b.vrefp` defaults to `0.9` V; valid range: vrefp > vrefn; sets positive conversion reference.
- `pipeline_adc_chain_4b.vrefn` defaults to `0.0` V; valid range: vrefn < vrefp; sets negative conversion reference.
- `pipeline_adc_chain_4b.vth` defaults to `0.45` V; valid range: finite real within the intended clock logic range; sets voltage-coded clock and bit decision threshold.
- `pipeline_adc_chain_4b.tedge` defaults to `1e-10` s; valid range: tedge > 0; sets residue and bit-output transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_CLOCKED_SAMPLE_HOLD`: restore: On each rising CLK crossing, the converter samples VIN and updates all stage residues and bits; outputs hold between conversions. Required traces: `time`, `clk`, `vin`, `res1`, `res2`, `s1b1`, `s1b0`, `s2b1`, `s2b0`, `dout3`, `dout2`, `dout1`, `dout0`.
- `P_STAGE1_DECISION`: restore: Stage 1 clips VIN to vrefn through vrefp, selects the correct quarter-scale bin, and exposes the two-bit coarse decision on S1B1/S1B0. Required traces: `time`, `clk`, `vin`, `s1b1`, `s1b0`.
- `P_STAGE1_RESIDUE`: restore: RES1 is four times the clipped sampled-input error from the selected stage-1 bin center, clipped to the conversion range. Required traces: `time`, `vin`, `s1b1`, `s1b0`, `res1`.
- `P_STAGE2_DECISION`: restore: Stage 2 applies the same quarter-scale two-bit decision to RES1 and exposes it on S2B1/S2B0. Required traces: `time`, `res1`, `s2b1`, `s2b0`.
- `P_STAGE2_RESIDUE`: restore: RES2 is four times the stage-2 input error from its selected bin center, clipped to the conversion range. Required traces: `time`, `res1`, `s2b1`, `s2b0`, `res2`.
- `P_FINAL_CODE_CONCATENATION`: restore: DOUT3/DOUT2 equal the stage-1 bits and DOUT1/DOUT0 equal the stage-2 bits, using VDD for high and VSS for low. Required traces: `time`, `vdd`, `vss`, `s1b1`, `s1b0`, `s2b1`, `s2b0`, `dout3`, `dout2`, `dout1`, `dout0`.

## Modeling Constraints

- Use deterministic rising-edge sampled two-stage quarter-scale conversion.
- Use rail-referenced smoothed voltage outputs for residues and bits.
- Do not hard-code validation points or use current contributions, transistor-level devices, AC/noise analysis, ddt, idt, or validation side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `pipeline_adc_chain_4b.va`.
Every supplied `.va` file is editable; do not add or omit files.
