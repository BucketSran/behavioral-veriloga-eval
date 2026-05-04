# Task: Pseudo-Random Source Generator

Design a Verilog-A module named `pseudo_random_source` that implements a 31-bit feedback shift register producing a pseudo-random bit sequence on its output port.

## Port Interface

| Port       | Direction  | Description                                                              |
|------------|------------|--------------------------------------------------------------------------|
| `supply_hi` | inout      | Positive supply rail (0.9V typical)                                      |
| `supply_lo` | inout      | Ground / negative supply rail (0V)                                       |
| `advance`   | input      | Clock input — rising edge shifts the register                            |
| `init_n`    | input      | Active-low asynchronous reset. When low, initializes the register state. |
| `run`       | input      | Enable signal. The register only updates on rising edges of `advance` when both `init_n` and `run` are high. |
| `prbs_out`  | output     | Pseudo-random binary sequence output drives to `supply_hi` or `supply_lo` |

## Functional Requirements

### Initialization Block

On the initial step of simulation, and on any negative-going crossing of `init_n` through 0.5V:

1. Set the switching threshold for the clock input to 0.5V.
2. Load an integer seed parameter into the register: bit position *i* receives the *i*-th bit of the seed value. The seed parameter defaults to 123.
3. After seeding, force bits at positions 0, 5, 10, 15, 20, 25, 30 to logic-1, overwriting whatever the seed placed there. This ensures the register never enters the all-zeros state.
4. Set the output level: if the most significant bit (position 31) is 1, drive `prbs_out` to `V(supply_hi)`; otherwise drive it to `V(supply_lo)`.

### Advance (Shift) Block

On every rising edge of `advance` crossing 0.5V, when `init_n` is above 0.5V (i.e., not in reset):

1. Shift all register bits one position toward the higher index (bit *i* moves to bit *i+1*).
2. Compute the new bit 0 as the XOR of the bits at feedback positions **31, 21, 1, and 0** (these four specific bit indices must be XOR-ed together and fed back into position 0).
3. After updating the register, set the output level as before: `prbs_out` drives to `V(supply_hi)` if bit 31 is 1, else to `V(supply_lo)`.

### Output Transition

The `prbs_out` port must use the `transition()` analog operator with a 50ps rise time and 50ps fall time when changing levels, with zero initial delay.

## Parameter

| Parameter | Type    | Default | Description                                          |
|-----------|---------|---------|------------------------------------------------------|
| `seed`    | integer | 123     | Initial value loaded into the register at reset time |

## Negative Constraints

- **This is NOT a CRC generator** — do not use a fixed seed with no feedback. The register must incorporate active feedback from the feedback positions on every clock edge.
- **This is NOT a Gold code generator** — only one shift register chain, not two. There is exactly one feedback loop feeding the first bit of a single 31-bit register.
- **The feedback positions must be configurable via parameters, not hardcoded constants** — use integer parameter(s) to specify which bit positions participate in the XOR feedback, rather than embedding the positions directly as unchangeable constants in expressions.

## Public Evaluation Contract

```
simulator lang=spectre
global 0
ahdl_include "pseudo_random_source.va"
Vvdd (supply_hi 0) vsource dc=0.9
Vvss (supply_lo 0) vsource dc=0.0
Vclk (advance 0) vsource type=pulse val0=0 val1=0.9 period=1n width=0.5n rise=50p fall=50p
Vrstb (init_n 0) vsource type=pwl wave=[0 0 100.9n 0 101n 0.9 500n 0.9]
Ven (run 0) vsource dc=0.9
IDUT (prbs_out supply_hi supply_lo advance run init_n) pseudo_random_source seed=123
tran tran stop=500n maxstep=2n
save advance init_n prbs_out
```
