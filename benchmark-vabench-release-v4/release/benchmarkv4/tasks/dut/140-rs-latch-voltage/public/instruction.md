# RS Latch Voltage

## Task Contract
Implement the Verilog-A DUT `rs_latch_voltage.va` for a voltage-coded set/reset latch support cell.

## Public Verilog-A Interface
Provide `module rs_latch_voltage(vin_s, vin_r, vout_q, vout_qbar);` with electrical inputs `vin_s`, `vin_r` and electrical outputs `vout_q`, `vout_qbar`.

## Public Parameter Contract
This task has no public parameters.

## Required Behavior
Interpret set and reset as logic 1 above 0.45 V. Initialize Q low. A set-only input drives Q high, a reset-only input drives Q low, and the hold condition preserves the previous state. Drive `vout_qbar` as the complement of Q. Use 0.9 V for high and 0.0 V for low.

## Modeling Constraints
Use a retained internal state in an analog block. Do not treat hold as reset, swap set and reset roles, or drive `qbar` independently of Q.

## Output Contract
Submit only the completed Verilog-A module in `rs_latch_voltage.va`.
