# Capacitive Weighted SAR Feedback DAC Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Capacitive Weighted SAR Feedback DAC` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `cdac_cal.va`:
  - Module `cdac_cal` (entry)
    - position 0: `VDD` (input, electrical)
    - position 1: `VSS` (input, electrical)
    - position 2: `CLK` (input, electrical)
    - position 3: `D9` (input, electrical)
    - position 4: `D8` (input, electrical)
    - position 5: `D7` (input, electrical)
    - position 6: `D6` (input, electrical)
    - position 7: `D5` (input, electrical)
    - position 8: `D4` (input, electrical)
    - position 9: `D3` (input, electrical)
    - position 10: `D2` (input, electrical)
    - position 11: `D1` (input, electrical)
    - position 12: `D0` (input, electrical)
    - position 13: `CAL0` (input, electrical)
    - position 14: `CAL1` (input, electrical)
    - position 15: `VDAC_P` (output, electrical)
    - position 16: `VDAC_N` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `cdac_cal` as `XDUT` with ordered public binding: VDD=VDD, VSS=VSS, CLK=CLK, D9=D9, D8=D8, D7=D7, D6=D6, D5=D5, D4=D4, D3=D3, D2=D2, D1=D1, D0=D0, CAL0=CAL0, CAL1=CAL1, VDAC_P=VDAC_P, VDAC_N=VDAC_N.

## Public Parameter Contract

- `cdac_cal.vcm` defaults to `0.45` V; valid range: V(VSS) <= vcm <= V(VDD); sets output common mode.
- `cdac_cal.swing` defaults to `0.6` V; valid range: swing >= 0; sets differential output swing scale.
- `cdac_cal.tt` defaults to `2e-11` s; valid range: tt > 0; sets output transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_CLOCKED_HOLD`: exercise and make observable: The DAC samples code and calibration inputs on rising CLK edges and holds the resulting output between edges. Required traces: `time`, `CLK`, `D9`, `D8`, `D7`, `D6`, `D5`, `D4`, `D3`, `D2`, `D1`, `D0`, `CAL0`, `CAL1`, `VDAC_P`, `VDAC_N`.
- `P_CODE_MONOTONICITY`: exercise and make observable: Increasing effective code increases VDAC_P minus VDAC_N. Required traces: `time`, `CLK`, `D9`, `D8`, `D7`, `D6`, `D5`, `D4`, `D3`, `D2`, `D1`, `D0`, `CAL0`, `CAL1`, `VDAC_P`, `VDAC_N`.
- `P_CALIBRATION_WEIGHT`: exercise and make observable: CAL0 contributes one calibration unit, CAL1 contributes two, and each unit offsets the main code by 32 codes. Required traces: `time`, `CLK`, `CAL0`, `CAL1`, `VDAC_P`, `VDAC_N`.
- `P_DIFFERENTIAL_COMMON_MODE`: exercise and make observable: VDAC_P and VDAC_N are complementary about vcm. Required traces: `time`, `VDAC_P`, `VDAC_N`.

The required trace names are: `time`, `VDD`, `VSS`, `CLK`, `D9`, `D8`, `D7`, `D6`, `D5`, `D4`, `D3`, `D2`, `D1`, `D0`, `CAL0`, `CAL1`, `VDAC_P`, `VDAC_N`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
