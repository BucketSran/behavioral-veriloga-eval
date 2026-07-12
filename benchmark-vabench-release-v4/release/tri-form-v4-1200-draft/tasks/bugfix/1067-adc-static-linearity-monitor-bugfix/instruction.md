# ADC Static Linearity Monitor Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `adc_static_linearity_monitor.va`:
  - Module `adc_static_linearity_monitor` (entry)
    - position 0: `vsample` (input, electrical)
    - position 1: `vin` (input, electrical)
    - position 2: `d2` (input, electrical)
    - position 3: `d1` (input, electrical)
    - position 4: `d0` (input, electrical)
    - position 5: `maxerr` (output, electrical)

## Public Parameter Contract

- `adc_static_linearity_monitor.vref` defaults to `1.0` V; valid range: vref > 0; sets the full-scale range used to derive the ideal three-bit bin-floor code.
- `adc_static_linearity_monitor.vth` defaults to `0.45` V; valid range: vth > 0; sets the threshold for vsample and observed output-bit decoding.
- `adc_static_linearity_monitor.lsb_out` defaults to `1.0` V/code; valid range: lsb_out > 0; scales each retained code-error LSB into the maxerr output voltage.
- `adc_static_linearity_monitor.tr` defaults to `2e-11` s; valid range: tr > 0; sets maxerr output transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_STROBE_UPDATE`: restore: The retained error metric updates only on rising crossings of vsample through vth and holds between strobes. Required traces: `time`, `vsample`, `vin`, `d2`, `d1`, `d0`, `maxerr`.
- `P_IDEAL_CODE`: restore: At a strobe, vin is clipped to 0 through vref and mapped to the ideal three-bit bin-floor code. Required traces: `time`, `vsample`, `vin`, `maxerr`.
- `P_OBSERVED_CODE`: restore: At a strobe, d2 through d0 are threshold-decoded as an unsigned three-bit word with d2 as MSB and d0 as LSB. Required traces: `time`, `vsample`, `d2`, `d1`, `d0`, `maxerr`.
- `P_ABSOLUTE_ERROR`: restore: Each sampled error is the absolute difference in codes between the ideal and observed three-bit words. Required traces: `time`, `vsample`, `vin`, `d2`, `d1`, `d0`, `maxerr`.
- `P_MAX_RETENTION`: restore: maxerr never decreases during a run and represents the largest sampled absolute code error seen so far. Required traces: `time`, `vsample`, `maxerr`.
- `P_METRIC_SCALE`: restore: maxerr equals the retained maximum code error multiplied by lsb_out, with smoothing set by tr. Required traces: `time`, `maxerr`.

## Modeling Constraints

- Use deterministic sampled voltage-domain behavior and retain state across strobes.
- Treat d2 as the MSB and d0 as the LSB in every code calculation.
- Do not encode stimulus times, private sample vectors, or checker tolerances in the DUT.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `adc_static_linearity_monitor.va`.
Every supplied `.va` file is editable; do not add or omit files.
