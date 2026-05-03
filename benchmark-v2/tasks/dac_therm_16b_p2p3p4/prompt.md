# Task: weighted_sum_converter

Design a Verilog-A module named `weighted_sum_converter` that reads 16 digital input lines, counts how many are active (above threshold), and drives an analog output voltage equal to the count multiplied by a fixed step voltage.

## Module Interface

| Port | Direction | Description |
|------|-----------|-------------|
| active_lines[15:0] | input | 16-line input bus; each line is a digital signal |
| clear | input | Active-low reset; when low, output forced to zero |
| level_out | output | Analog output voltage = (active count) * vstep |

## Behavioral Specification

1. The module continuously counts how many `active_lines` have voltage above the threshold `vth`.
2. When `clear` is below `vth` (logic low), `level_out` is forced to 0V.
3. When `clear` is above `vth`, `level_out` = (number of active lines) * `vstep`.
4. Output must use `transition()` for smooth transitions.

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| vstep | 1.0 | Output voltage increment per active line |
| tr | 10p | Output transition rise/fall time |
| vth | 0.4 | Input logic threshold voltage |

## Constraints

- Must be pure voltage-domain
- Use `transition()` for output
- Do NOT use current-domain constructs

## Negative Constraints

- The output voltage must be linearly proportional to the count of active lines ¡ª NOT binary-weighted
- Do NOT implement an R-2R ladder or current-steering DAC architecture
- The output must be monotonic with respect to the number of active lines

## Public Evaluation Contract

```spectre
simulator lang=spectre
global 0
Vclear (clear 0) vsource type=pwl wave=[0 0  4e-9 0  5e-9 0.9  2000e-9 0.9]
Val0 (active_lines[0] 0) vsource type=pwl wave=[0 0  200e-9 0  205e-9 0.9]
Val1 (active_lines[1] 0) vsource type=pwl wave=[0 0  200e-9 0  205e-9 0.9]
// (all 16 lines follow the same pattern, 4 lines activating every 200ns)
tran tran stop=2000n maxstep=1n
save clear level_out
```

## Deliverables
Write your module to `dut.va`.
