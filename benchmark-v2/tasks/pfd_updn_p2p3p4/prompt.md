# Task: edge_arrival_comparator

Design a Verilog-A module named `edge_arrival_comparator` that compares the arrival times of rising edges on two digital input signals.

## Module Interface

```verilog-a
module edge_arrival_comparator(
    inout electrical supply_hi, inout electrical supply_lo,
    input electrical early_edge, input electrical late_edge,
    output electrical adv, output electrical ret
);
```

**Parameters:**
- `vth = 0.45` -- threshold voltage for edge detection
- `tedge = 50p` -- transition time for output signals

**Port descriptions:**
- `supply_hi` / `supply_lo` -- power supply rails (nominally 0.9V / 0V)
- `early_edge` -- first event input (nominally connected to a signal whose edges may arrive earlier)
- `late_edge` -- second event input (nominally connected to a signal whose edges may arrive later)
- `adv` -- indicator output; goes to the supply_hi voltage when the rising edge on early_edge arrives first
- `ret` -- indicator output; goes to the supply_hi voltage when the rising edge on late_edge arrives first

## Functional Behavior

This is a module with two event inputs and two indicator outputs. The indicator corresponding to the input whose rising edge arrives first goes high. When both indicators are high, they are immediately cleared (reset to supply_lo voltage). This allows the module to continuously track which input's rising edge arrives first on each cycle.

The module operates as follows:
1. On each rising edge of `early_edge` (detected when V(early_edge) crosses above vth), the `adv` output is set high.
2. On each rising edge of `late_edge` (detected when V(late_edge) crosses above vth), the `ret` output is set high.
3. If both `adv` and `ret` would be high at the same time (which occurs when the second of the two edges arrives while the first indicator is still active), both outputs are immediately reset low. This reset must happen within the same event that detects the second edge.
4. Outputs transition between supply_lo and supply_hi voltages with a transition time of `tedge`, using the `transition()` analog filter.

## Constraints

- This is NOT an XOR phase detector -- do NOT compute the XOR of input levels.
- This is NOT a Bang-Bang phase detector -- do NOT sample with a clock.
- This is NOT an SR latch -- the reset path must be combinational, not clock-synchronized. Both indicators are cleared as an immediate consequence of the second edge arriving, without waiting for any external clock.
- Both outputs must never be high simultaneously. The reset must occur within the same event that causes both to be high, preventing any observable simultaneous-high state at the outputs.

## Public Evaluation Contract

Your design will be evaluated with the following Spectre testbench:

```
simulator lang=spectre
global 0
Vvdd (supply_hi 0) vsource dc=0.9 type=dc
Vvss (supply_lo 0) vsource dc=0.0 type=dc
Vearly (early_edge 0) vsource type=pulse val0=0 val1=0.9 period=20n width=10n rise=100p fall=100p
Vlate (late_edge 0) vsource type=pulse val0=0 val1=0.9 period=20n delay=3n width=10n rise=100p fall=100p
IDUT (supply_hi supply_lo early_edge late_edge adv ret) edge_arrival_comparator vth=0.45 tedge=50p
simulatorOptions options reltol=1e-4 vabstol=1e-6 iabstol=1e-12 temp=27 tnom=27 gmin=1e-12
tran tran stop=300n maxstep=100p errpreset=conservative
save early_edge late_edge adv ret
ahdl_include "./dut.va"
```

The testbench applies two periodic pulse signals: `early_edge` with no delay and `late_edge` with a 3ns delay. The rising edge on `early_edge` arrives before the rising edge on `late_edge`, so `adv` should pulse high and `ret` should remain low. The outputs must satisfy:
- `adv` produces a positive pulse each cycle when early_edge leads
- `adv` and `ret` are never simultaneously at the supply_hi voltage

Your Verilog-A file should be named `dut.va` and must compile and simulate correctly with the testbench above.
