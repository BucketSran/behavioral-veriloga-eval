# Task: adpll_ratio_hop_smoke

Write a pure voltage-domain Verilog-A behavioral ADPLL that uses a timer-driven DCO and a programmable feedback divider.

Requirements:

1. Ports must be `electrical` only.
2. The module must take a reference clock input and an analog `ratio_ctrl` input whose rounded value sets the divider ratio in the range 2 to 16.
3. The DCO frequency must be adjusted by an internal digital control code so the divided feedback clock tracks the reference.
4. Expose:
   - `vout` as the DCO clock output
   - `fb_clk` as the divided feedback clock
   - `vctrl_mon` as a normalized monitor of the control code
   - `lock` as a streak-based lock indicator
5. The reference testbench will step `ratio_ctrl` from 4 to 6 during transient and expects the ADPLL to relock.

The implementation should use `@(cross())`, `@(timer())`, and `transition()` and stay compatible with EVAS and Spectre-style voltage-domain behavioral modeling.
