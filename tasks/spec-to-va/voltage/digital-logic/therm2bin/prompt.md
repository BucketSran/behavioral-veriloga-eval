Write a Verilog-A thermometer-to-binary encoder.

Module name: `therm2bin_ref`. 15-bit thermometer input, 4-bit binary output. Handle bubble errors (non-monotonic thermometer codes) gracefully.

Ports:
- `therm_0`: input electrical
- `therm_1`: input electrical
- `therm_2`: input electrical
- `therm_3`: input electrical
- `therm_4`: input electrical
- `therm_5`: input electrical
- `therm_6`: input electrical
- `therm_7`: input electrical
- `therm_8`: input electrical
- `therm_9`: input electrical
- `therm_10`: input electrical
- `therm_11`: input electrical
- `therm_12`: input electrical
- `therm_13`: input electrical
- `therm_14`: input electrical
- `bin_0`: output electrical
- `bin_1`: output electrical
- `bin_2`: output electrical
- `bin_3`: output electrical

Implement this in Verilog-A behavioral modeling.
