# Dither Adder Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Dither Adder` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `dither_adder.va`:
  - Module `dither_adder` (entry)
    - position 0: `VRES_P` (input, electrical)
    - position 1: `VRES_N` (input, electrical)
    - position 2: `DPN` (input, electrical)
    - position 3: `VOUT_P` (output, electrical)
    - position 4: `VOUT_N` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `dither_adder` as `XDUT` with ordered public binding: VRES_P=vres_p, VRES_N=vres_n, DPN=dpn, VOUT_P=vout_p, VOUT_N=vout_n.

## Public Parameter Contract

- `dither_adder.vdd` defaults to `0.9` V; valid range: vdd > 0; preserves the public compatibility supply-domain parameter.
- `dither_adder.vth` defaults to `0.45` V; valid range: finite real; sets the DPN polarity threshold.
- `dither_adder.DITHER_AMP` defaults to `0.014063` V differential; valid range: DITHER_AMP >= 0; sets the magnitude of the injected differential dither.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_POSITIVE_DITHER`: exercise and make observable: When DPN is above vth, the output differential exceeds the input differential by DITHER_AMP. Required traces: `time`, `vres_p`, `vres_n`, `dpn`, `vout_p`, `vout_n`.
- `P_NEGATIVE_DITHER`: exercise and make observable: When DPN is at or below vth, the output differential is lower than the input differential by DITHER_AMP. Required traces: `time`, `vres_p`, `vres_n`, `dpn`, `vout_p`, `vout_n`.
- `P_SYMMETRIC_SPLIT`: exercise and make observable: Half of the selected differential dither is added to VOUT_P and half is subtracted from VOUT_N. Required traces: `time`, `vres_p`, `vres_n`, `dpn`, `vout_p`, `vout_n`.
- `P_COMMON_MODE_PRESERVATION`: exercise and make observable: The output pair preserves the input common mode and does not introduce a vdd/2 offset. Required traces: `time`, `vres_p`, `vres_n`, `vout_p`, `vout_n`.
- `P_PARAMETER_OVERRIDE`: exercise and make observable: Legal DITHER_AMP and vth overrides change only dither magnitude and polarity decision as declared. Required traces: `time`, `dpn`, `vres_p`, `vres_n`, `vout_p`, `vout_n`.

The required trace names are: `time`, `vres_p`, `vres_n`, `dpn`, `vout_p`, `vout_n`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
