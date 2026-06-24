# Agent-Visible Spec: vbr1_l1_rf_mixer_downconverter_macro:dut

One-shot DUT-generation task for `RF mixer/downconverter macro`.

## Agent-Visible Input

- `tb_rf_mixer_downconverter_macro.scs`

## Required Output

- `rf_mixer_downconverter_macro.va`

## Public Task Summary

- Level: `L1`
- Category: RF and AFE Behavioral Macromodels
- Domain: `voltage`
- Form: `dut`

## Public Observables

Saved signal names are part of the public contract: use actual top-level Spectre
nets connected to the DUT; do not rely on instance-qualified aliases.

- Inherited from the public harness

If `time` is present, it is the implicit transient waveform axis.

## Form-Specific Requirements

- Implement only the requested Verilog-A DUT artifact(s); do not generate a Spectre testbench in this form.
- Preserve the public module names, port order, parameters, and waveform observable names.

## Public Verilog-A Interface

- `rf_mixer_downconverter_macro.va` declares module `rf_mixer_downconverter_macro` with positional ports: `clk`, `rst`, `vin`, `out`, `metric`.

## Public Testbench And Observable Contract

Public transient setting used by the release harness:

```spectre
tran tran stop=80n maxstep=0.5n
```

The release harness expects these exact public scalar observables:

- `clk`
- `rst`
- `vin`
- `out`
- `metric`

When this form generates a testbench, use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

## Public Behavioral Targets

- Treat clk as the LO-polarity waveform with a 0.45 V logic threshold.
- Convert the input envelope around 0.45 V common mode to baseband by flipping sign with LO polarity.
- Preserve output common mode near 0.45 V and keep out bounded.
- metric should indicate active conversion or LO polarity state.

## Output Contract

Return exactly one source artifact named `rf_mixer_downconverter_macro.va`.
Do not include explanatory prose outside the source artifact contents.

## Task-Specific Public Description

### RF mixer/downconverter macro (spec-to-va)

Write the Verilog-A behavioral module only.

Behavioral intent:

Model a voltage-domain RF mixer/downconverter where the LO polarity modulates the RF input around common mode into a baseband output.

Module name: `rf_mixer_downconverter_macro`.
Domain: pure voltage-domain behavioral Verilog-A.
Do not use current contributions, transistor-level devices, AC/noise analysis,
or KCL/KVL solving assumptions.

This is a voltage-domain RF/AFE behavioral macromodel task. Model observable gain, compression, LO polarity, RSSI, limiting, AGC, or I/Q baseband behavior with event-driven voltage states. Do not implement transistor RF physics, S-parameters, current-domain loads, communication modem algorithms, or full link-level decoding.

Public port contract:

```verilog
module rf_mixer_downconverter_macro(clk, rst, vin, out, metric);
input clk, rst, vin;
output out, metric;
electrical clk, rst, vin, out, metric;
```

Signal contract:

clk is the public LO-polarity waveform and rst is voltage-coded reset. vin is an RF input envelope around 0.45 V common mode. out is the LO-polarity-converted baseband voltage. metric marks active conversion.

Saved waveform columns:

```text
clk rst vin out metric
```

Public transient contract:

```spectre
tran tran stop=80n maxstep=0.5n
```

## Modeling Constraints

Keep the implementation in the public voltage-domain behavioral Verilog-A task
scope. Do not emit hidden checker logic, private thresholds, private sample
windows, gold answers, current-domain device models, transistor-level circuits,
or AC/noise analysis assumptions unless they are explicitly part of the public
task contract.
