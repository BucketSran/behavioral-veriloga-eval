# Charge Pump Abstraction Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Charge Pump Abstraction` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `charge_pump_abstraction.va`:
  - Module `charge_pump_abstraction` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `up` (input, electrical)
    - position 3: `dn` (input, electrical)
    - position 4: `vctrl` (output, electrical)
    - position 5: `metric` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `charge_pump_abstraction` as `XDUT` with ordered public binding: clk=clk, rst=rst, up=up, dn=dn, vctrl=vctrl, metric=metric.

## Public Parameter Contract

- `charge_pump_abstraction.tr` defaults to `1e-10` s; valid range: tr > 0; sets output transition smoothing.
- `charge_pump_abstraction.vth` defaults to `0.45` V; valid range: finite real; sets clk, rst, up, and dn logic threshold.
- `charge_pump_abstraction.step` defaults to `0.06` V; valid range: step > 0; sets control-voltage movement per sampled exclusive request.
- `charge_pump_abstraction.vmin` defaults to `0.05` V; valid range: vmin < vmax; sets lower vctrl clamp.
- `charge_pump_abstraction.vmax` defaults to `0.85` V; valid range: vmax > vmin; sets upper vctrl clamp.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_MIDSCALE`: exercise and make observable: When rst is high, vctrl resets to the midpoint of vmin and vmax and metric is 0.45 V. Required traces: `time`, `rst`, `vctrl`, `metric`.
- `P_UP_ONLY_STEP`: exercise and make observable: A rising clock crossing sampling up high and dn low increases vctrl by step and encodes metric at 0.75 V. Required traces: `time`, `clk`, `rst`, `up`, `dn`, `vctrl`, `metric`.
- `P_DN_ONLY_STEP`: exercise and make observable: A rising clock crossing sampling dn high and up low decreases vctrl by step and encodes metric at 0.15 V. Required traces: `time`, `clk`, `rst`, `up`, `dn`, `vctrl`, `metric`.
- `P_HOLD_CASES`: exercise and make observable: A rising clock crossing sampling both or neither request holds vctrl and encodes metric at 0.45 V. Required traces: `time`, `clk`, `rst`, `up`, `dn`, `vctrl`, `metric`.
- `P_CONTROL_CLAMP`: exercise and make observable: Repeated sampled movement cannot drive vctrl below vmin or above vmax. Required traces: `time`, `clk`, `up`, `dn`, `vctrl`.
- `P_SAMPLED_HOLD`: exercise and make observable: Changes on up or dn between rising clock crossings do not immediately change vctrl. Required traces: `time`, `clk`, `up`, `dn`, `vctrl`.

The required trace names are: `time`, `clk`, `rst`, `up`, `dn`, `vctrl`, `metric`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
