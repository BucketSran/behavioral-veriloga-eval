# Hysteresis Trip Characterizer Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Hysteresis Trip Characterizer` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `hysteresis_trip_characterizer` as `XDUT` with ordered public binding: vdd=vdd, vss=vss, vin=vin, cmp_out=cmp_out, trip_rise=trip_rise, trip_fall=trip_fall, hyst_width=hyst_width, valid=valid.

## Public Parameter Contract

- `hysteresis_trip_characterizer.tr` defaults to `2e-11` s; valid range: tr >= 0; sets transition smoothing for captured trip values, hysteresis width, and valid.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_SUPPLY_MIDPOINT_THRESHOLD`: exercise and make observable: The characterizer detects cmp_out transitions through the instantaneous midpoint of vdd and vss. Required traces: `time`, `vdd`, `vss`, `cmp_out`.
- `P_RISING_TRIP_CAPTURE`: exercise and make observable: On each rising cmp_out midpoint crossing, trip_rise captures the instantaneous vin minus vss value. Required traces: `time`, `vss`, `vin`, `cmp_out`, `trip_rise`.
- `P_FALLING_TRIP_CAPTURE`: exercise and make observable: On each falling cmp_out midpoint crossing, trip_fall captures the instantaneous vin minus vss value. Required traces: `time`, `vss`, `vin`, `cmp_out`, `trip_fall`.
- `P_LATEST_EDGE_REFRESH`: exercise and make observable: Later rising or falling transitions refresh the corresponding captured trip value rather than leaving only the first measurement. Required traces: `time`, `vin`, `cmp_out`, `trip_rise`, `trip_fall`.
- `P_HYSTERESIS_WIDTH_SIGN`: exercise and make observable: After both directions are captured, hyst_width equals trip_rise minus trip_fall with that signed polarity. Required traces: `time`, `trip_rise`, `trip_fall`, `hyst_width`.
- `P_VALID_AFTER_BOTH_DIRECTIONS`: exercise and make observable: Valid remains at vss until at least one rising and one falling trip have been captured, then rises to vdd. Required traces: `time`, `vdd`, `vss`, `cmp_out`, `valid`.

The required trace names are: `time`, `vdd`, `vss`, `vin`, `cmp_out`, `trip_rise`, `trip_fall`, `hyst_width`, `valid`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
