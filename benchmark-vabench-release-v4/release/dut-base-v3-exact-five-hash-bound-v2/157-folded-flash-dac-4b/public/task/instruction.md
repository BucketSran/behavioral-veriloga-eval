# Folded Flash DAC 4b

## Task Contract
Implement the Verilog-A DUT `folded_flash_dac_4b.va` for a voltage-coded folded 4-bit DAC transfer.

## Public Verilog-A Interface
Provide `module folded_flash_dac_4b(vd4, vd3, vd2, vd1, vout);` with electrical inputs `vd4`, `vd3`, `vd2`, `vd1` and electrical output `vout`.

## Public Parameter Contract
Expose real parameters `vref = 1`, `trise = 1p`, `tfall = 1p`, `tdel = 0`, and `vtrans = 0.45` with the ranges declared in the starter file. Testbenches may override these parameters.

## Required Behavior
Decode the inputs as voltage-coded bits. Use `vd4` as the folding MSB and `vd3:vd1` as the lower subcode. When the folding MSB is high, add the subcode above the fold center; when it is low, mirror the subcode below the fold center. Drive `vout = vref * folded_code / 16.0`, where `folded_code` is the folded 4-bit code after that mirror operation.

## Modeling Constraints
Update on input threshold crossings or initial step and drive a smooth analog output. Do not remove the fold mirror, use the wrong denominator, invert the MSB fold direction, or treat the input as a plain binary DAC.

## Output Contract
Submit only the completed Verilog-A module in `folded_flash_dac_4b.va`.
