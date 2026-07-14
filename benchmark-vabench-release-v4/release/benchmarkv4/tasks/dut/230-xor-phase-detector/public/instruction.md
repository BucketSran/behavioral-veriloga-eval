# XOR Phase Detector

## Task Contract

Implement `xor_phase_detector.va` as a combinational XOR-style phase detector for voltage-coded clocks.

## Public Verilog-A Interface

Use this module signature:

```verilog
module xor_phase_detector(ref, fb, up, down);
```

All ports are scalar `electrical` nodes. `ref` and `fb` are voltage-coded clock inputs. `up` and `down` are voltage-coded detector outputs.

## Public Parameter Contract

- `vdd`: high level for outputs and threshold reference, default `1.2`.

## Required Behavior

- Interpret `ref` and `fb` logic levels using a threshold of `vdd/2`.
- Drive `up` high when the interpreted `ref` and `fb` levels differ.
- Drive `down` high when the interpreted `ref` and `fb` levels match.
- Update outputs combinationally from the current input voltages.

## Modeling Constraints

Use voltage contributions only. Do not use current contributions, transistor-level devices, AC/noise analysis, checker logic, out-of-band test hooks, or simulator side channels.

## Output Contract

Return exactly one source artifact named `xor_phase_detector.va`.
