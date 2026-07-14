# ADC Static Linearity Monitor Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `ADC Static Linearity Monitor` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `adc_static_linearity_monitor.va`:
  - Module `adc_static_linearity_monitor` (entry)
    - position 0: `vsample` (input, electrical)
    - position 1: `vin` (input, electrical)
    - position 2: `d2` (input, electrical)
    - position 3: `d1` (input, electrical)
    - position 4: `d0` (input, electrical)
    - position 5: `maxerr` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `adc_static_linearity_monitor` as `XDUT` with ordered public binding: vsample=vsample, vin=vin, d2=d2, d1=d1, d0=d0, maxerr=maxerr.

## Public Parameter Contract

- `adc_static_linearity_monitor.vref` defaults to `1.0` V; valid range: vref > 0; sets the full-scale range used to derive the ideal three-bit bin-floor code.
- `adc_static_linearity_monitor.vth` defaults to `0.45` V; valid range: vth > 0; sets the threshold for vsample and observed output-bit decoding.
- `adc_static_linearity_monitor.lsb_out` defaults to `1.0` V/code; valid range: lsb_out > 0; scales each retained code-error LSB into the maxerr output voltage.
- `adc_static_linearity_monitor.tr` defaults to `2e-11` s; valid range: tr > 0; sets maxerr output transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_STROBE_UPDATE`: exercise and make observable: The retained error metric updates only on rising crossings of vsample through vth and holds between strobes. Required traces: `time`, `vsample`, `vin`, `d2`, `d1`, `d0`, `maxerr`.
- `P_IDEAL_CODE`: exercise and make observable: At a strobe, vin is clipped to 0 through vref and mapped to the ideal three-bit bin-floor code. Required traces: `time`, `vsample`, `vin`, `maxerr`.
- `P_OBSERVED_CODE`: exercise and make observable: At a strobe, d2 through d0 are threshold-decoded as an unsigned three-bit word with d2 as MSB and d0 as LSB. Required traces: `time`, `vsample`, `d2`, `d1`, `d0`, `maxerr`.
- `P_ABSOLUTE_ERROR`: exercise and make observable: Each sampled error is the absolute difference in codes between the ideal and observed three-bit words. Required traces: `time`, `vsample`, `vin`, `d2`, `d1`, `d0`, `maxerr`.
- `P_MAX_RETENTION`: exercise and make observable: maxerr never decreases during a run and represents the largest sampled absolute code error seen so far. Required traces: `time`, `vsample`, `maxerr`.
- `P_METRIC_SCALE`: exercise and make observable: maxerr equals the retained maximum code error multiplied by lsb_out, with smoothing set by tr. Required traces: `time`, `maxerr`.

The required trace names are: `time`, `vsample`, `vin`, `d2`, `d1`, `d0`, `maxerr`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
