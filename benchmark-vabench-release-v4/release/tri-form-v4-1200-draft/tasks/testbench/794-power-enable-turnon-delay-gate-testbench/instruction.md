# Power Enable Turn-On Delay Gate Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Power Enable Turn-On Delay Gate` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `power_enable_turnon_delay_gate.va`:
  - Module `power_enable_turnon_delay_gate` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `vdd` (input, electrical)
    - position 2: `vss` (input, electrical)
    - position 3: `vbias` (input, electrical)
    - position 4: `en` (input, electrical)
    - position 5: `pd` (input, electrical)
    - position 6: `pwr_ok` (output, electrical)
    - position 7: `drive_en` (output, electrical)
    - position 8: `delay_mon` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `power_enable_turnon_delay_gate` as `XDUT` with ordered public binding: clk=clk, vdd=vdd, vss=vss, vbias=vbias, en=en, pd=pd, pwr_ok=pwr_ok, drive_en=drive_en, delay_mon=delay_mon.

## Public Parameter Contract

- `power_enable_turnon_delay_gate.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `power_enable_turnon_delay_gate.vhi` defaults to `0.9`; valid range: finite; overrides vhi.
- `power_enable_turnon_delay_gate.vdd_min` defaults to `0.75`; valid range: finite; overrides vdd_min.
- `power_enable_turnon_delay_gate.vdd_max` defaults to `1.05`; valid range: finite; overrides vdd_max.
- `power_enable_turnon_delay_gate.vbias_min` defaults to `0.25`; valid range: finite; overrides vbias_min.
- `power_enable_turnon_delay_gate.vbias_max` defaults to `0.75`; valid range: finite; overrides vbias_max.
- `power_enable_turnon_delay_gate.delay_cycles` defaults to `3`; valid range: finite; overrides delay_cycles.
- `power_enable_turnon_delay_gate.tr` defaults to `60p`; valid range: finite; overrides tr.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_EACH_RISING_CROSSING_OF_CLK`: exercise and make observable: On each rising crossing of `clk`, evaluate whether supply, bias, enable, and power-down conditions allow operation. Drive `pwr_ok` high whenever the sampled conditions are valid, meaning `vdd_min <= V(vdd, vss) <= vdd_max`, `vbias_min <= V(vbias, vss) <= vbias_max`, `V(en) > vth`, and `V(pd) <= vth`. Maintain an integer consecutive-valid counter. Increment the counter by one on each sampled valid rising-clock update until it reaches `delay_cycles`; reset the counter to zero on any sampled invalid update. After applying that update, assert `drive_en` when the counter is greater than or equal to `delay_cycles`. Drive `delay_mon = min(vhi, vhi * counter / delay_cycles)` as the bounded voltage-coded turn-on progress value from `0 V` to `vhi`. Smooth all outputs with `transition()`. Required traces: `time`, `clk`, `delay_mon`, `drive_en`, `en`, `pd`, `pwr_ok`, `vbias`, `vdd`, `vss`.
- `P_BUILD_A_VOLTAGE_DOMAIN_POWER_SEQUENCING`: exercise and make observable: Build a voltage-domain power sequencing DUT for a biased analog block. The module samples supply, bias, enable, and power-down conditions, reports sampled power validity, and releases downstream drive only after a consecutive valid turn-on delay. Required traces: `time`, `clk`, `delay_mon`, `drive_en`, `en`, `pd`, `pwr_ok`, `vbias`, `vdd`, `vss`.
- `P_VTH_0_45_V_LOGIC_THRESHOLD`: exercise and make observable: `vth = 0.45 V`: logic threshold for `clk`, `en`, and `pd`. Required traces: `time`, `clk`, `delay_mon`, `drive_en`, `en`, `pd`, `pwr_ok`, `vbias`, `vdd`, `vss`.
- `P_VHI_0_9_V_HIGH_LEVEL`: exercise and make observable: `vhi = 0.9 V`: high level for voltage-coded outputs. Required traces: `time`, `clk`, `delay_mon`, `drive_en`, `en`, `pd`, `pwr_ok`, `vbias`, `vdd`, `vss`.
- `P_VDD_MIN_0_75_V_VDD`: exercise and make observable: `vdd_min = 0.75 V`, `vdd_max = 1.05 V`: valid `V(vdd, vss)` window. Required traces: `time`, `clk`, `delay_mon`, `drive_en`, `en`, `pd`, `pwr_ok`, `vbias`, `vdd`, `vss`.
- `P_VBIAS_MIN_0_25_V_VBIAS`: exercise and make observable: `vbias_min = 0.25 V`, `vbias_max = 0.75 V`: valid `V(vbias, vss)` window. Required traces: `time`, `clk`, `delay_mon`, `drive_en`, `en`, `pd`, `pwr_ok`, `vbias`, `vdd`, `vss`.

The required trace names are: `time`, `clk`, `delay_mon`, `drive_en`, `en`, `pd`, `pwr_ok`, `vbias`, `vdd`, `vss`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
