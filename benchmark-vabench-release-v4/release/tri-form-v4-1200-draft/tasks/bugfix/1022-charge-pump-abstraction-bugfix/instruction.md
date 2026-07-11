# Charge Pump Abstraction Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `charge_pump_abstraction.va`:
  - Module `charge_pump_abstraction` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `up` (input, electrical)
    - position 3: `dn` (input, electrical)
    - position 4: `vctrl` (output, electrical)
    - position 5: `metric` (output, electrical)

## Public Parameter Contract

- `charge_pump_abstraction.tr` defaults to `1e-10` s; valid range: tr > 0; sets output transition smoothing.
- `charge_pump_abstraction.vth` defaults to `0.45` V; valid range: finite real; sets clk, rst, up, and dn logic threshold.
- `charge_pump_abstraction.step` defaults to `0.06` V; valid range: step > 0; sets control-voltage movement per sampled exclusive request.
- `charge_pump_abstraction.vmin` defaults to `0.05` V; valid range: vmin < vmax; sets lower vctrl clamp.
- `charge_pump_abstraction.vmax` defaults to `0.85` V; valid range: vmax > vmin; sets upper vctrl clamp.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_MIDSCALE`: restore: When rst is high, vctrl resets to the midpoint of vmin and vmax and metric is 0.45 V. Required traces: `time`, `rst`, `vctrl`, `metric`.
- `P_UP_ONLY_STEP`: restore: A rising clock crossing sampling up high and dn low increases vctrl by step and encodes metric at 0.75 V. Required traces: `time`, `clk`, `rst`, `up`, `dn`, `vctrl`, `metric`.
- `P_DN_ONLY_STEP`: restore: A rising clock crossing sampling dn high and up low decreases vctrl by step and encodes metric at 0.15 V. Required traces: `time`, `clk`, `rst`, `up`, `dn`, `vctrl`, `metric`.
- `P_HOLD_CASES`: restore: A rising clock crossing sampling both or neither request holds vctrl and encodes metric at 0.45 V. Required traces: `time`, `clk`, `rst`, `up`, `dn`, `vctrl`, `metric`.
- `P_CONTROL_CLAMP`: restore: Repeated sampled movement cannot drive vctrl below vmin or above vmax. Required traces: `time`, `clk`, `up`, `dn`, `vctrl`.
- `P_SAMPLED_HOLD`: restore: Changes on up or dn between rising clock crossings do not immediately change vctrl. Required traces: `time`, `clk`, `up`, `dn`, `vctrl`.

## Modeling Constraints

- Represent charge-pump requests as sampled voltage-domain state updates.
- Use voltage contributions only.
- Do not use current contributions, ddt(), idt(), transistor-level devices, or validation side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `charge_pump_abstraction.va`.
Every supplied `.va` file is editable; do not add or omit files.
