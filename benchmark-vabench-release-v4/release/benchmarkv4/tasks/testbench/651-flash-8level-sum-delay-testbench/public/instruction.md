# Flash 8level Sum Delay Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Flash 8level Sum Delay` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `flash_8level_sum_delay.va`:
  - Module `flash_8level_sum_delay` (entry)
    - position 0: `vip` (input, electrical)
    - position 1: `vim` (input, electrical)
    - position 2: `clks` (input, electrical)
    - position 3: `reset` (input, electrical)
    - position 4: `refp` (input, electrical)
    - position 5: `refn` (input, electrical)
    - position 6: `doutsum` (output, electrical)
    - position 7: `doutsumdelay` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `flash_8level_sum_delay` as `XDUT` with ordered public binding: vip=vip, vim=vim, clks=clks, reset=reset, refp=refp, refn=refn, doutsum=doutsum, doutsumdelay=doutsumdelay.

## Public Parameter Contract

- `flash_8level_sum_delay.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `flash_8level_sum_delay.ref_scaling` defaults to `0.5`; valid range: finite; overrides ref_scaling.
- `flash_8level_sum_delay.tt` defaults to `10p`; valid range: finite; overrides tt.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_CLOCKED_FLASH_THRESHOLD_SUM`: exercise and make observable: Each rising `clks` crossing compares `V(vip,vim)` against the symmetric flash thresholds and updates `doutsum`. Required traces: `time`, `clks`, `doutsum`, `doutsumdelay`, `refn`, `refp`, `reset`, `vim`, `vip`.
- `P_REFERENCE_SCALING`: exercise and make observable: The flash thresholds use `V(refp)-V(refn)` multiplied by `ref_scaling`. Required traces: `time`, `clks`, `doutsum`, `doutsumdelay`, `refn`, `refp`, `reset`, `vim`, `vip`.
- `P_ONE_CYCLE_DELAYED_SUM`: exercise and make observable: `doutsumdelay` reports the previous sampled flash summary, not the current summary. Required traces: `time`, `clks`, `doutsum`, `doutsumdelay`, `refn`, `refp`, `reset`, `vim`, `vip`.
- `P_NORMALIZED_OUTPUT`: exercise and make observable: The flash summary is normalized by the eight-level count before being driven. Required traces: `time`, `clks`, `doutsum`, `doutsumdelay`, `refn`, `refp`, `reset`, `vim`, `vip`.

The required trace names are: `time`, `clks`, `doutsum`, `doutsumdelay`, `refn`, `refp`, `reset`, `vim`, `vip`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
