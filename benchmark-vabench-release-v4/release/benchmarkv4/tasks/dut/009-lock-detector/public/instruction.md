# Lock Detector

## Task Contract

Implement the requested Verilog-A artifact for `Lock Detector`.
- Form: `dut`
- Level: `L1`
- Category: `pll_clock_timing`
- Target artifact(s): `lock_detector.va`

Implement one Verilog-A DUT file named `lock_detector.va`.

The DUT is a voltage-domain reference/feedback lock detector for a PLL-style clock path. It observes rising edges on `ref_clk` and `fb_clk`, uses an active-low reset, and drives a scalar `lock` output.

## Public Verilog-A Interface

The file must define module `lock_detector` with this exact positional port order:

```verilog
module lock_detector(
    ref_clk, fb_clk, rst_n, lock
);
    input ref_clk, fb_clk, rst_n;
    output lock;
    electrical ref_clk, fb_clk, rst_n, lock;
```

Use voltage-domain `electrical` ports. Treat logic low as below `vth` and logic high as above `vth`.

## Public Parameter Contract

Provide these overrideable public parameters:

- `vth = 0.45 V`: logic threshold for `ref_clk`, `fb_clk`, and `rst_n`.
- `vdd = 0.9 V`: logic high output level for `lock`.
- `tol = 2 ns`: maximum allowed time separation between a reference rising edge and the most recent feedback rising edge.
- `need = 3`: number of consecutive aligned reference events required before asserting lock.
- `tr = 500 ps`: transition smoothing time for `lock`.

## Required Behavior

- `rst_n` is active low. While reset is low, clear the consecutive-hit counter and drive `lock` low.
- On every rising edge of `fb_clk`, record that feedback edge time.
- Feedback edges observed while `rst_n` is low must not count toward a later post-reset lock sequence.
- On every rising edge of `ref_clk` while reset is high, compare the reference edge time with the most recent feedback rising edge time.
- A reference event is aligned only when the most recent feedback rising edge is within `tol` of that reference rising edge.
- Assert `lock` only after `need` consecutive aligned reference events.
- Before the `need`th consecutive aligned reference event, `lock` must remain low.
- Any reference event whose most recent feedback edge is outside the `tol` window breaks the streak and drives `lock` low.
- A later active-low reset must clear an already asserted lock and require `need` new consecutive aligned reference events before reassertion.

Use voltage contributions for `lock`, preferably with `transition(...)`. Do not use current contributions, `ddt()`, or `idt()`.

## Modeling Constraints

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one source artifact named `lock_detector.va`. Do not generate a testbench for this task.
