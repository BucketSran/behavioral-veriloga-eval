# Config Shift Register 64b Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Config Shift Register 64b` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `config_shift_reg_64b.va`:
  - Module `config_shift_reg_64b` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst_n` (input, electrical)
    - position 2: `serial_in` (input, electrical)
    - position 3: `q[63]` (output, electrical)
    - position 4: `q[62]` (output, electrical)
    - position 5: `q[61]` (output, electrical)
    - position 6: `q[60]` (output, electrical)
    - position 7: `q[59]` (output, electrical)
    - position 8: `q[58]` (output, electrical)
    - position 9: `q[57]` (output, electrical)
    - position 10: `q[56]` (output, electrical)
    - position 11: `q[55]` (output, electrical)
    - position 12: `q[54]` (output, electrical)
    - position 13: `q[53]` (output, electrical)
    - position 14: `q[52]` (output, electrical)
    - position 15: `q[51]` (output, electrical)
    - position 16: `q[50]` (output, electrical)
    - position 17: `q[49]` (output, electrical)
    - position 18: `q[48]` (output, electrical)
    - position 19: `q[47]` (output, electrical)
    - position 20: `q[46]` (output, electrical)
    - position 21: `q[45]` (output, electrical)
    - position 22: `q[44]` (output, electrical)
    - position 23: `q[43]` (output, electrical)
    - position 24: `q[42]` (output, electrical)
    - position 25: `q[41]` (output, electrical)
    - position 26: `q[40]` (output, electrical)
    - position 27: `q[39]` (output, electrical)
    - position 28: `q[38]` (output, electrical)
    - position 29: `q[37]` (output, electrical)
    - position 30: `q[36]` (output, electrical)
    - position 31: `q[35]` (output, electrical)
    - position 32: `q[34]` (output, electrical)
    - position 33: `q[33]` (output, electrical)
    - position 34: `q[32]` (output, electrical)
    - position 35: `q[31]` (output, electrical)
    - position 36: `q[30]` (output, electrical)
    - position 37: `q[29]` (output, electrical)
    - position 38: `q[28]` (output, electrical)
    - position 39: `q[27]` (output, electrical)
    - position 40: `q[26]` (output, electrical)
    - position 41: `q[25]` (output, electrical)
    - position 42: `q[24]` (output, electrical)
    - position 43: `q[23]` (output, electrical)
    - position 44: `q[22]` (output, electrical)
    - position 45: `q[21]` (output, electrical)
    - position 46: `q[20]` (output, electrical)
    - position 47: `q[19]` (output, electrical)
    - position 48: `q[18]` (output, electrical)
    - position 49: `q[17]` (output, electrical)
    - position 50: `q[16]` (output, electrical)
    - position 51: `q[15]` (output, electrical)
    - position 52: `q[14]` (output, electrical)
    - position 53: `q[13]` (output, electrical)
    - position 54: `q[12]` (output, electrical)
    - position 55: `q[11]` (output, electrical)
    - position 56: `q[10]` (output, electrical)
    - position 57: `q[9]` (output, electrical)
    - position 58: `q[8]` (output, electrical)
    - position 59: `q[7]` (output, electrical)
    - position 60: `q[6]` (output, electrical)
    - position 61: `q[5]` (output, electrical)
    - position 62: `q[4]` (output, electrical)
    - position 63: `q[3]` (output, electrical)
    - position 64: `q[2]` (output, electrical)
    - position 65: `q[1]` (output, electrical)
    - position 66: `q[0]` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `config_shift_reg_64b` as `XDUT` with ordered public binding: clk=clk, rst_n=rst_n, serial_in=serial_in, q[63]=q63, q[62]=q62, q[61]=q61, q[60]=q60, q[59]=q59, q[58]=q58, q[57]=q57, q[56]=q56, q[55]=q55, q[54]=q54, q[53]=q53, q[52]=q52, q[51]=q51, q[50]=q50, q[49]=q49, q[48]=q48, q[47]=q47, q[46]=q46, q[45]=q45, q[44]=q44, q[43]=q43, q[42]=q42, q[41]=q41, q[40]=q40, q[39]=q39, q[38]=q38, q[37]=q37, q[36]=q36, q[35]=q35, q[34]=q34, q[33]=q33, q[32]=q32, q[31]=q31, q[30]=q30, q[29]=q29, q[28]=q28, q[27]=q27, q[26]=q26, q[25]=q25, q[24]=q24, q[23]=q23, q[22]=q22, q[21]=q21, q[20]=q20, q[19]=q19, q[18]=q18, q[17]=q17, q[16]=q16, q[15]=q15, q[14]=q14, q[13]=q13, q[12]=q12, q[11]=q11, q[10]=q10, q[9]=q9, q[8]=q8, q[7]=q7, q[6]=q6, q[5]=q5, q[4]=q4, q[3]=q3, q[2]=q2, q[1]=q1, q[0]=q0.

## Public Parameter Contract

- `config_shift_reg_64b.vdd` defaults to `0.9` V; valid range: vdd > 0; sets the voltage-coded parallel-output high level.
- `config_shift_reg_64b.vth` defaults to `0.45` V; valid range: 0 < vth < vdd; sets the clock, reset, and serial-input decision threshold.
- `config_shift_reg_64b.tr` defaults to `2e-11` s; valid range: tr > 0; sets parallel-output transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ACTIVE_LOW_RESET`: exercise and make observable: On a rising clock crossing with rst_n low, every q bit is cleared to logic low. Required traces: `time`, `clk`, `rst_n`, `q0`, `q1`, `q2`, `q3`, `q4`, `q5`, `q6`, `q7`, `q8`, `q9`, `q10`, `q11`, `q12`, `q13`, `q14`, `q15`, `q16`, `q17`, `q18`, `q19`, `q20`, `q21`, `q22`, `q23`, `q24`, `q25`, `q26`, `q27`, `q28`, `q29`, `q30`, `q31`, `q32`, `q33`, `q34`, `q35`, `q36`, `q37`, `q38`, `q39`, `q40`, `q41`, `q42`, `q43`, `q44`, `q45`, `q46`, `q47`, `q48`, `q49`, `q50`, `q51`, `q52`, `q53`, `q54`, `q55`, `q56`, `q57`, `q58`, `q59`, `q60`, `q61`, `q62`, `q63`.
- `P_SERIAL_SHIFT_DIRECTION`: exercise and make observable: On each rising clock crossing with rst_n high, serial_in enters q[0], previous q[N] moves to q[N+1], and previous q[62] moves to q[63]. Required traces: `time`, `clk`, `rst_n`, `serial_in`, `q0`, `q1`, `q2`, `q3`, `q4`, `q5`, `q6`, `q7`, `q8`, `q9`, `q10`, `q11`, `q12`, `q13`, `q14`, `q15`, `q16`, `q17`, `q18`, `q19`, `q20`, `q21`, `q22`, `q23`, `q24`, `q25`, `q26`, `q27`, `q28`, `q29`, `q30`, `q31`, `q32`, `q33`, `q34`, `q35`, `q36`, `q37`, `q38`, `q39`, `q40`, `q41`, `q42`, `q43`, `q44`, `q45`, `q46`, `q47`, `q48`, `q49`, `q50`, `q51`, `q52`, `q53`, `q54`, `q55`, `q56`, `q57`, `q58`, `q59`, `q60`, `q61`, `q62`, `q63`.
- `P_ONE_SHIFT_PER_EDGE`: exercise and make observable: Exactly one register-position shift occurs for each qualifying rising clock crossing. Required traces: `time`, `clk`, `rst_n`, `serial_in`, `q0`, `q1`, `q2`, `q3`, `q4`, `q5`, `q6`, `q7`, `q8`, `q9`, `q10`, `q11`, `q12`, `q13`, `q14`, `q15`, `q16`, `q17`, `q18`, `q19`, `q20`, `q21`, `q22`, `q23`, `q24`, `q25`, `q26`, `q27`, `q28`, `q29`, `q30`, `q31`, `q32`, `q33`, `q34`, `q35`, `q36`, `q37`, `q38`, `q39`, `q40`, `q41`, `q42`, `q43`, `q44`, `q45`, `q46`, `q47`, `q48`, `q49`, `q50`, `q51`, `q52`, `q53`, `q54`, `q55`, `q56`, `q57`, `q58`, `q59`, `q60`, `q61`, `q62`, `q63`.
- `P_HOLD_BETWEEN_EDGES`: exercise and make observable: The parallel register state holds between rising clock crossings despite changes on serial_in. Required traces: `time`, `clk`, `serial_in`, `q0`, `q1`, `q2`, `q3`, `q4`, `q5`, `q6`, `q7`, `q8`, `q9`, `q10`, `q11`, `q12`, `q13`, `q14`, `q15`, `q16`, `q17`, `q18`, `q19`, `q20`, `q21`, `q22`, `q23`, `q24`, `q25`, `q26`, `q27`, `q28`, `q29`, `q30`, `q31`, `q32`, `q33`, `q34`, `q35`, `q36`, `q37`, `q38`, `q39`, `q40`, `q41`, `q42`, `q43`, `q44`, `q45`, `q46`, `q47`, `q48`, `q49`, `q50`, `q51`, `q52`, `q53`, `q54`, `q55`, `q56`, `q57`, `q58`, `q59`, `q60`, `q61`, `q62`, `q63`.
- `P_OUTPUT_LEVELS`: exercise and make observable: Each q bit uses 0 V for logic low and vdd for logic high with finite transition smoothing. Required traces: `time`, `q0`, `q1`, `q2`, `q3`, `q4`, `q5`, `q6`, `q7`, `q8`, `q9`, `q10`, `q11`, `q12`, `q13`, `q14`, `q15`, `q16`, `q17`, `q18`, `q19`, `q20`, `q21`, `q22`, `q23`, `q24`, `q25`, `q26`, `q27`, `q28`, `q29`, `q30`, `q31`, `q32`, `q33`, `q34`, `q35`, `q36`, `q37`, `q38`, `q39`, `q40`, `q41`, `q42`, `q43`, `q44`, `q45`, `q46`, `q47`, `q48`, `q49`, `q50`, `q51`, `q52`, `q53`, `q54`, `q55`, `q56`, `q57`, `q58`, `q59`, `q60`, `q61`, `q62`, `q63`.

The required trace names are: `time`, `clk`, `rst_n`, `serial_in`, `q0`, `q1`, `q2`, `q3`, `q4`, `q5`, `q6`, `q7`, `q8`, `q9`, `q10`, `q11`, `q12`, `q13`, `q14`, `q15`, `q16`, `q17`, `q18`, `q19`, `q20`, `q21`, `q22`, `q23`, `q24`, `q25`, `q26`, `q27`, `q28`, `q29`, `q30`, `q31`, `q32`, `q33`, `q34`, `q35`, `q36`, `q37`, `q38`, `q39`, `q40`, `q41`, `q42`, `q43`, `q44`, `q45`, `q46`, `q47`, `q48`, `q49`, `q50`, `q51`, `q52`, `q53`, `q54`, `q55`, `q56`, `q57`, `q58`, `q59`, `q60`, `q61`, `q62`, `q63`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
