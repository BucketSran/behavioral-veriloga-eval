# Divide By 8/9 Switch

## Task Contract
Implement the Verilog-A DUT `divide_by_8_9_switch.va` for a modulus-switched voltage-domain clock divider.

## Public Verilog-A Interface
Provide `module divide_by_8_9_switch(clkin, mc, out);` with electrical inputs `clkin`, `mc` and electrical output `out`.

## Public Parameter Contract
Expose real parameters `tdel = 10p`, `tr = 10p`, `tf = 10p`, `vdd = 1.2`, and `vth = 0.6`. Testbenches may override these parameters.

## Required Behavior
Initialize the divider in divide-by-8 mode with `out` low; the first post-initial rising `clkin` crossing enters the high output window. Count rising crossings of `clkin` through `vth`. Use divide-by-8 mode while `mc` is low and switch to divide-by-9 mode while `mc` is high. Wrap the counter modulo the active divisor and drive `out` high for count values 0 through 3, low otherwise.

## Modeling Constraints
Use event-driven counter state and detect both rising and falling crossings of `mc` to change modulus. Do not get stuck in divide-by-9 mode, use the wrong duty window, half the high level, or derive the waveform from fixed time samples.

## Output Contract
Submit only the completed Verilog-A module in `divide_by_8_9_switch.va`.
