# Comparator Delay Overdrive Meter Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Comparator Delay Overdrive Meter` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `comparator_delay_overdrive_meter.va`:
  - Module `comparator_delay_overdrive_meter` (entry)
    - position 0: `vdd` (input, electrical)
    - position 1: `vss` (input, electrical)
    - position 2: `clk` (input, electrical)
    - position 3: `vinp` (input, electrical)
    - position 4: `vinn` (input, electrical)
    - position 5: `outp` (input, electrical)
    - position 6: `outn` (input, electrical)
    - position 7: `delay_ps` (output, electrical)
    - position 8: `overdrive_mv` (output, electrical)
    - position 9: `polarity` (output, electrical)
    - position 10: `valid` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `comparator_delay_overdrive_meter` as `XDUT` with ordered public binding: vdd=vdd, vss=vss, clk=clk, vinp=vinp, vinn=vinn, outp=outp, outn=outn, delay_ps=delay_ps, overdrive_mv=overdrive_mv, polarity=polarity, valid=valid.

## Public Parameter Contract

- `comparator_delay_overdrive_meter.tr` defaults to `20p`; valid range: finite; overrides tr.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_CLOCK_ARMED_MEASUREMENT`: exercise and make observable: Each rising `clk` threshold crossing stores the launch time, captures absolute differential overdrive, and arms exactly one pending measurement. Required traces: `time`, `clk`, `vinp`, `vinn`, `overdrive_mv`, `valid`.
- `P_DECISION_DELAY_CAPTURE`: exercise and make observable: The first qualifying `outp` or `outn` decision edge while armed reports the elapsed clock-to-decision delay in `delay_ps`. Required traces: `time`, `clk`, `outp`, `outn`, `delay_ps`, `valid`.
- `P_ABSOLUTE_OVERDRIVE_METRIC`: exercise and make observable: `overdrive_mv` reports the absolute input differential magnitude at launch time. Required traces: `time`, `clk`, `vinp`, `vinn`, `overdrive_mv`.
- `P_POLARITY_AND_VALID_FLAG`: exercise and make observable: `polarity` reports the winning output decision direction and `valid` asserts only for a completed armed measurement. Required traces: `time`, `outp`, `outn`, `polarity`, `valid`.

The required trace names are: `time`, `clk`, `vinp`, `vinn`, `outp`, `outn`, `delay_ps`, `overdrive_mv`, `polarity`, `valid`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
