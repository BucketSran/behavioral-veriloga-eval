# Hysteresis Trip Characterizer Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `hysteresis_trip_characterizer.va`:
  - Module `hysteresis_trip_characterizer` (entry)
    - position 0: `vdd` (input, electrical)
    - position 1: `vss` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `cmp_out` (input, electrical)
    - position 4: `trip_rise` (output, electrical)
    - position 5: `trip_fall` (output, electrical)
    - position 6: `hyst_width` (output, electrical)
    - position 7: `valid` (output, electrical)

## Public Parameter Contract

- `hysteresis_trip_characterizer.tr` defaults to `2e-11` s; valid range: tr >= 0; sets transition smoothing for captured trip values, hysteresis width, and valid.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_SUPPLY_MIDPOINT_THRESHOLD`: restore: The characterizer detects cmp_out transitions through the instantaneous midpoint of vdd and vss. Required traces: `time`, `vdd`, `vss`, `cmp_out`.
- `P_RISING_TRIP_CAPTURE`: restore: On each rising cmp_out midpoint crossing, trip_rise captures the instantaneous vin minus vss value. Required traces: `time`, `vss`, `vin`, `cmp_out`, `trip_rise`.
- `P_FALLING_TRIP_CAPTURE`: restore: On each falling cmp_out midpoint crossing, trip_fall captures the instantaneous vin minus vss value. Required traces: `time`, `vss`, `vin`, `cmp_out`, `trip_fall`.
- `P_LATEST_EDGE_REFRESH`: restore: Later rising or falling transitions refresh the corresponding captured trip value rather than leaving only the first measurement. Required traces: `time`, `vin`, `cmp_out`, `trip_rise`, `trip_fall`.
- `P_HYSTERESIS_WIDTH_SIGN`: restore: After both directions are captured, hyst_width equals trip_rise minus trip_fall with that signed polarity. Required traces: `time`, `trip_rise`, `trip_fall`, `hyst_width`.
- `P_VALID_AFTER_BOTH_DIRECTIONS`: restore: Valid remains at vss until at least one rising and one falling trip have been captured, then rises to vdd. Required traces: `time`, `vdd`, `vss`, `cmp_out`, `valid`.

## Modeling Constraints

- Treat the companion hysteretic comparator as a supplied harness component observed only through vin and cmp_out.
- Capture trip values on both cmp_out edge polarities and drive reported values with smoothed voltage contributions.
- Do not use current contributions, ddt(), idt(), validation hooks, hard-coded waveform sample points, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `hysteresis_trip_characterizer.va`.
Every supplied `.va` file is editable; do not add or omit files.
