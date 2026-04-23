Write a 4-bit static analog-to-binary converter module named _va_d2b_4b.

Module name: `_va_d2b_4b`. Input: analog voltage VIN (range VSS to VDD). Output: 4-bit binary code DOUT[3:0]. No clock — purely combinational, continuous tracking. Use VDD/VSS power ports.

Ports:
- `VDD`: inout electrical
- `VSS`: inout electrical
- `VIN`: input electrical
- `DOUT3`: output electrical
- `DOUT2`: output electrical
- `DOUT1`: output electrical
- `DOUT0`: output electrical

Implement this in Verilog-A behavioral modeling.
