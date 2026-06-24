# Agent-Visible Spec: vbr1_l2_flash_adc_mini_array:e2e

One-shot end-to-end task for `Flash ADC mini-array`.

## Agent-Visible Input

- None

## Required Output

- `flash_adc_3b.va`
- `tb_flash_adc_3b_ref.scs`

## Public Task Summary

- Level: `L2`
- Category: Data Converter Models
- Domain: `voltage`
- Form: `e2e`

## Public Observables

Saved signal names are part of the public contract: use actual top-level Spectre
nets connected to the DUT; do not rely on instance-qualified aliases.

- Inherited from the public harness

If `time` is present, it is the implicit transient waveform axis.

## L2 Background And Claim Boundary

This Level-2 row is a behavioral composition/flow task for Flash ADC mini-array. It should expose intermediate state, multi-stage behavior, or a closed-loop relation through the public observables below.
Stay within the listed voltage-domain/event-driven contract. Do not use transistor-level devices, current-domain loads, AC/noise analysis, S-parameters, or hidden checker logic unless the public contract explicitly lists them.
Paper-facing claims for this row are limited to the public behavior checks below; do not broaden the task into full silicon implementation, layout, device physics, or unlisted performance metrics.

## Form-Specific Requirements

- Generate all target artifacts: `flash_adc_3b.va`, `tb_flash_adc_3b_ref.scs`.
- The Spectre testbench must exercise the generated DUT/system through public observables; do not generate hidden checker logic.
- The generated Verilog-A file(s) `flash_adc_3b.va` must be co-located with the generated Spectre testbench.
- Include the generated DUT exactly with `ahdl_include "flash_adc_3b.va"` in the generated testbench.
- Use Spectre AHDL instance syntax with the instance name first and module name last: `XNAME (node1 node2 ...) module_name`.
- Never write module-first syntax such as `module_name instance_name (...)`; that is not the release Spectre testbench syntax.

## Public Verilog-A Interface

- `flash_adc_3b.va` declares module `flash_adc_3b` with positional ports: `VDD`, `VSS`, `VIN`, `CLK`, `CMP0`, `CMP1`, `CMP2`, `CMP3`, `CMP4`, `CMP5`, `CMP6`, `DOUT2`, `DOUT1`, `DOUT0`.

## Public Testbench And Observable Contract

Public transient setting used by the release harness:

```spectre
tran tran stop=86n maxstep=200p
```

The release harness expects these exact public scalar observables:

- `vin`
- `clk`
- `cmp0`
- `cmp1`
- `cmp2`
- `cmp3`
- `cmp4`
- `cmp5`
- `cmp6`
- `dout2`
- `dout1`
- `dout0`

When this form generates a testbench, use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Public stimulus/source nodes visible in the reference harness include:

- `vdd`
- `vss`
- `vin`
- `clk`

## Public Spectre Testbench Scaffold

When this form generates a `.scs` testbench, use the following public skeleton shape. Fill in only the public stimulus details required by the task; do not copy or emit hidden checker logic.

```spectre
simulator lang=spectre
global 0
ahdl_include "flash_adc_3b.va"

Vvdd (vdd 0) vsource dc=0.9 type=dc
Vvss (vss 0) vsource dc=0.0 type=dc

IDUT (vdd vss vin clk cmp0 cmp1 cmp2 cmp3 cmp4 cmp5 cmp6 dout2 dout1 dout0) flash_adc_3b vrefp=0.9 vrefn=0.0 vth=0.45 tedge=100p

tran tran stop=86n maxstep=200p
save vin clk cmp0 cmp1 cmp2 cmp3 cmp4 cmp5 cmp6 dout2 dout1 dout0
```

Critical syntax rules:

- Every Verilog-A DUT/support file used by the testbench must have a literal `ahdl_include "<file>.va"` line in the `.scs` artifact.
- Spectre AHDL instances use instance-first/module-last syntax: `XNAME (node1 node2 ...) module_name`.
- Do not use module-first syntax such as `module_name instance_name (...)`.
- Keep saved names as plain scalar public observables, not instance-qualified aliases.

## Public L2 Behavior Contract

This row is a small flash ADC array, so the public behavior must include both
parallel comparator decisions and binary encoding:

1. Comparator ladder:
   - Implement seven comparator outputs `cmp0` through `cmp6`.
   - Use evenly ordered thresholds across the 0 V to 0.9 V input range.
   - For each sampled `vin`, the comparator outputs should form a thermometer
     prefix: all lower-threshold comparators high, all higher-threshold
     comparators low.

2. Clocked sampling:
   - Update comparator and binary outputs on rising `clk` crossings after the
     input has been stable.
   - Use 0 V/0.9 V logic levels and a 0.45 V logic threshold.

3. Binary encoder:
   - Drive `dout2 dout1 dout0` as the 3-bit binary count represented by the
     thermometer prefix.
   - The testbench should present one stable input in each of the eight
     quantization bins so all output codes 0 through 7 are visible.

The expected public waveform relation is: `vin` bin -> thermometer prefix on
`cmp0..cmp6` -> matching binary count on `dout2..dout0`.

## Output Contract

Return exactly these source artifacts:

- `flash_adc_3b.va`
- `tb_flash_adc_3b_ref.scs`

Do not include explanatory prose outside the source artifact contents.

## Task-Specific Public Description


Create a pure voltage-domain 3-bit flash ADC mini-array. The DUT must expose
the seven comparator decisions as a thermometer vector and encode that vector
into a 3-bit binary output after clocked sampling.

## DUT Contract

- Module name: `flash_adc_3b`
- Ports, all `electrical`, exactly in this order: `VDD`, `VSS`, `VIN`, `CLK`, `CMP0`, `CMP1`, `CMP2`, `CMP3`, `CMP4`, `CMP5`, `CMP6`, `DOUT2`, `DOUT1`, `DOUT0`
- Parameters:
  - `vrefp` real, default `0.9`
  - `vrefn` real, default `0.0`
  - `vth` real, default `0.45`
  - `tedge` real, default `100p`
- Behavior:
  - Full-scale range is `vrefn` to `vrefp`, divided into 8 equal bins.
  - On each rising `clk` edge, compare `V(vin)` against the seven thresholds
    `vrefn + k*(vrefp-vrefn)/8` for `k=1..7`.
  - Drive `cmp0` through `cmp6` as the latched threshold-comparator decisions,
    where `cmp0` is the 1-LSB threshold and `cmp6` is the 7-LSB threshold.
  - The comparator outputs must form a thermometer prefix: higher thresholds
    cannot be high unless all lower thresholds are high.
  - Encode the number of high comparator outputs into `dout2:dout1:dout0`,
    with `dout2` as MSB and `dout0` as LSB.
  - Output HIGH should be `V(vdd)` and output LOW should be `V(vss)`.
  - Use `@(cross(V(clk) - vth, +1))` and `transition(...)`.

## Testbench Contract

- Use a 0.9 V supply and 0 V reference.
- Drive `vin` through the midpoint of each of the 8 quantization bins, using
  stable windows before each clock edge.
- Drive `clk` so the checker can sample one stable conversion for every code
  from `0` through `7`.
- Instantiate the DUT by positional ports.
- Save these exact scalar names: `vin`, `clk`, `cmp0`, `cmp1`, `cmp2`, `cmp3`, `cmp4`, `cmp5`, `cmp6`, `dout2`, `dout1`, `dout0`.
- Include the generated DUT file `flash_adc_3b.va`.

## Modeling Constraints

Keep the implementation in the public voltage-domain behavioral Verilog-A task
scope. Do not emit hidden checker logic, private thresholds, private sample
windows, gold answers, current-domain device models, transistor-level circuits,
or AC/noise analysis assumptions unless they are explicitly part of the public
task contract.
