# Attenuator Gain

## Task Contract

Implement the requested Verilog-A artifact for `Attenuator Gain`.
- Form: `dut`
- Level: `L1`
- Category: `mixed_signal`
- Target artifact(s): `attenuator_gain.va`

- Base function: Voltage-domain attenuator with dB gain control
- Domain: `voltage`
- Output boundary: validation logic is external; do not generate validation harness or testbench, or measurement helper artifacts.

## Public Verilog-A Interface

`attenuator_gain.va` must declare:

```verilog
module attenuator_gain(vin, vout);
input vin;
output vout;
electrical vin, vout;
parameter real attenuation = 0;
```

## Public Parameter Contract

The public parameters declared by the target artifact are part of the contract and may be overridden by validation harnesses. Preserve their names, defaults, ranges, and meanings:

- `parameter real attenuation = 0;` in `attenuator_gain.va`.

## Required Behavior

Implement a continuous voltage attenuator. The `attenuation` parameter is in dB and controls the amplitude ratio. A 0 dB setting passes the input unchanged; positive attenuation reduces the output amplitude using the standard voltage dB relationship.

Drive `vout` as a voltage-domain output proportional to `vin`. Use Verilog-A real arithmetic and math operators for the dB-to-linear conversion. Do not use current contributions, transistor devices, or testbench-specific constants.

## Modeling Constraints

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one source artifact named `attenuator_gain.va`.
Do not include explanatory prose outside the source artifact contents.
