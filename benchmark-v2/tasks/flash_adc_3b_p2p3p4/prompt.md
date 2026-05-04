# Task: level_to_code_converter

Design a Verilog-A module named `level_to_code_converter` that maps a continuous input voltage to a 3-bit discrete code by dividing the full-scale range into 8 equal segments and determining which segment the input falls into, updated on each rising edge of a sampling command.

## Module Interface

| Port      | Direction          | Description                                      |
|-----------|--------------------|--------------------------------------------------|
| analog_level | input electrical   | Continuous input voltage to be digitized         |
| sample_strobe | input electrical   | Sampling command; code updates on rising edge    |
| qb2       | output electrical  | Most significant bit of the 3-bit code           |
| qb1       | output electrical  | Middle bit of the 3-bit code                     |
| qb0       | output electrical  | Least significant bit of the 3-bit code          |
| supply_hi | inout electrical   | Positive supply voltage                          |
| supply_lo | inout electrical   | Ground / negative supply                         |

## Parameters

| Parameter | Default | Description                        |
|-----------|---------|------------------------------------|
| ref_hi    | 0.9     | Upper bound of the input range     |
| ref_lo    | 0.0     | Lower bound of the input range     |
| vth       | 0.45    | Logic threshold for edge detection |
| tedge     | 100p    | Output transition time (seconds)   |

## Functional Requirements

This is a module that maps a continuous input voltage to a 3-bit discrete code by dividing the full-scale range into 8 equal segments and determining which segment the input falls into, updated on each rising edge of a sampling command.

- The full-scale input range [ref_lo, ref_hi] is divided into 8 uniform segments.
- At each rising edge of `sample_strobe` (detected when the signal crosses `vth`), the segment index corresponding to `analog_level` is computed.
- The 3-bit code is output on `qb2`, `qb1`, `qb0`, where `qb2` is the most significant bit and `qb0` is the least significant bit.
- Each output bit drives either `supply_hi` (logic high) or `supply_lo` (logic low).
- Output transitions must use `transition()` with rise/fall time `tedge`.
- Input voltages below the lower bound are clamped to the minimum code (0), and input voltages above the upper bound are clamped to the maximum code (7).
- The output code must be binary-weighted, NOT thermometer-coded.

## Explicit Constraints

- **This is NOT a SAR architecture** — do NOT use successive approximation.
- **This is NOT a pipeline architecture** — do NOT cascade stages.
- **The output code must be binary-weighted, NOT thermometer-coded.**
- **Do NOT use a comparator array or reference ladder** — this is a behavioral model using mathematical quantization.

## Public Evaluation Contract

The design will be validated with the following Spectre testbench:

```spectre
simulator lang=spectre
global 0
Vvdd (supply_hi 0) vsource dc=0.9 type=dc
Vvss (supply_lo 0) vsource dc=0.0 type=dc
Vvin (analog_level 0) vsource type=pwl wave=[0 0 800e-9 0.9]
Vclk (sample_strobe 0) vsource type=pulse val0=0 val1=0.9 period=10n width=5n rise=100p fall=100p
// DUT instantiation goes here
tran tran stop=820n maxstep=2n
save analog_level sample_strobe qb2 qb1 qb0
```

Your module will be placed at the path `dut.va` and will be verified with the above testbench.

### Expected Behavior

With the given testbench, the output should produce all 8 possible 3-bit codes (000 through 111) as `analog_level` ramps from 0 to 0.9 V, and the output codes should be monotonic (non-decreasing) over the ramp.

## Deliverables

Write your module to `dut.va` using standard Verilog-A syntax.
