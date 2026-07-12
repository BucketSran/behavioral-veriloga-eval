# Config Latch 32b Clocked Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `config_latch_32b.va`:
  - Module `config_latch_32b` (entry)
    - position 0: `en` (input, electrical)
    - position 1: `d[31]` (input, electrical)
    - position 2: `d[30]` (input, electrical)
    - position 3: `d[29]` (input, electrical)
    - position 4: `d[28]` (input, electrical)
    - position 5: `d[27]` (input, electrical)
    - position 6: `d[26]` (input, electrical)
    - position 7: `d[25]` (input, electrical)
    - position 8: `d[24]` (input, electrical)
    - position 9: `d[23]` (input, electrical)
    - position 10: `d[22]` (input, electrical)
    - position 11: `d[21]` (input, electrical)
    - position 12: `d[20]` (input, electrical)
    - position 13: `d[19]` (input, electrical)
    - position 14: `d[18]` (input, electrical)
    - position 15: `d[17]` (input, electrical)
    - position 16: `d[16]` (input, electrical)
    - position 17: `d[15]` (input, electrical)
    - position 18: `d[14]` (input, electrical)
    - position 19: `d[13]` (input, electrical)
    - position 20: `d[12]` (input, electrical)
    - position 21: `d[11]` (input, electrical)
    - position 22: `d[10]` (input, electrical)
    - position 23: `d[9]` (input, electrical)
    - position 24: `d[8]` (input, electrical)
    - position 25: `d[7]` (input, electrical)
    - position 26: `d[6]` (input, electrical)
    - position 27: `d[5]` (input, electrical)
    - position 28: `d[4]` (input, electrical)
    - position 29: `d[3]` (input, electrical)
    - position 30: `d[2]` (input, electrical)
    - position 31: `d[1]` (input, electrical)
    - position 32: `d[0]` (input, electrical)
    - position 33: `q[31]` (output, electrical)
    - position 34: `q[30]` (output, electrical)
    - position 35: `q[29]` (output, electrical)
    - position 36: `q[28]` (output, electrical)
    - position 37: `q[27]` (output, electrical)
    - position 38: `q[26]` (output, electrical)
    - position 39: `q[25]` (output, electrical)
    - position 40: `q[24]` (output, electrical)
    - position 41: `q[23]` (output, electrical)
    - position 42: `q[22]` (output, electrical)
    - position 43: `q[21]` (output, electrical)
    - position 44: `q[20]` (output, electrical)
    - position 45: `q[19]` (output, electrical)
    - position 46: `q[18]` (output, electrical)
    - position 47: `q[17]` (output, electrical)
    - position 48: `q[16]` (output, electrical)
    - position 49: `q[15]` (output, electrical)
    - position 50: `q[14]` (output, electrical)
    - position 51: `q[13]` (output, electrical)
    - position 52: `q[12]` (output, electrical)
    - position 53: `q[11]` (output, electrical)
    - position 54: `q[10]` (output, electrical)
    - position 55: `q[9]` (output, electrical)
    - position 56: `q[8]` (output, electrical)
    - position 57: `q[7]` (output, electrical)
    - position 58: `q[6]` (output, electrical)
    - position 59: `q[5]` (output, electrical)
    - position 60: `q[4]` (output, electrical)
    - position 61: `q[3]` (output, electrical)
    - position 62: `q[2]` (output, electrical)
    - position 63: `q[1]` (output, electrical)
    - position 64: `q[0]` (output, electrical)

## Public Parameter Contract

- `config_latch_32b.vdd` defaults to `0.9` V; valid range: vdd > 0; sets the voltage-coded output high level.
- `config_latch_32b.vth` defaults to `0.45` V; valid range: 0 < vth < vdd; sets the enable and data-bit decision threshold.
- `config_latch_32b.tr` defaults to `2e-11` s; valid range: tr > 0; sets output rise and fall smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_ENABLED_PASS`: restore: When en is high, every q bit equals the corresponding voltage-coded d bit. Required traces: `time`, `en`, `d0`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `d7`, `d8`, `d9`, `d10`, `d11`, `d12`, `d13`, `d14`, `d15`, `d16`, `d17`, `d18`, `d19`, `d20`, `d21`, `d22`, `d23`, `d24`, `d25`, `d26`, `d27`, `d28`, `d29`, `d30`, `d31`, `q0`, `q1`, `q2`, `q3`, `q4`, `q5`, `q6`, `q7`, `q8`, `q9`, `q10`, `q11`, `q12`, `q13`, `q14`, `q15`, `q16`, `q17`, `q18`, `q19`, `q20`, `q21`, `q22`, `q23`, `q24`, `q25`, `q26`, `q27`, `q28`, `q29`, `q30`, `q31`.
- `P_DISABLED_CLEAR`: restore: When en is low, every q bit is driven low regardless of the data input. Required traces: `time`, `en`, `d0`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `d7`, `d8`, `d9`, `d10`, `d11`, `d12`, `d13`, `d14`, `d15`, `d16`, `d17`, `d18`, `d19`, `d20`, `d21`, `d22`, `d23`, `d24`, `d25`, `d26`, `d27`, `d28`, `d29`, `d30`, `d31`, `q0`, `q1`, `q2`, `q3`, `q4`, `q5`, `q6`, `q7`, `q8`, `q9`, `q10`, `q11`, `q12`, `q13`, `q14`, `q15`, `q16`, `q17`, `q18`, `q19`, `q20`, `q21`, `q22`, `q23`, `q24`, `q25`, `q26`, `q27`, `q28`, `q29`, `q30`, `q31`.
- `P_STATIC_ENABLE_BEHAVIOR`: restore: The public interface is combinational enable gating: q follows data changes while enabled and does not retain a prior word while disabled. Required traces: `time`, `en`, `d0`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `d7`, `d8`, `d9`, `d10`, `d11`, `d12`, `d13`, `d14`, `d15`, `d16`, `d17`, `d18`, `d19`, `d20`, `d21`, `d22`, `d23`, `d24`, `d25`, `d26`, `d27`, `d28`, `d29`, `d30`, `d31`, `q0`, `q1`, `q2`, `q3`, `q4`, `q5`, `q6`, `q7`, `q8`, `q9`, `q10`, `q11`, `q12`, `q13`, `q14`, `q15`, `q16`, `q17`, `q18`, `q19`, `q20`, `q21`, `q22`, `q23`, `q24`, `q25`, `q26`, `q27`, `q28`, `q29`, `q30`, `q31`.
- `P_BIT_ALIGNMENT`: restore: Each d[N] controls only the same-index q[N]; bus order is not reversed or shifted. Required traces: `time`, `d0`, `d1`, `d2`, `d3`, `d4`, `d5`, `d6`, `d7`, `d8`, `d9`, `d10`, `d11`, `d12`, `d13`, `d14`, `d15`, `d16`, `d17`, `d18`, `d19`, `d20`, `d21`, `d22`, `d23`, `d24`, `d25`, `d26`, `d27`, `d28`, `d29`, `d30`, `d31`, `q0`, `q1`, `q2`, `q3`, `q4`, `q5`, `q6`, `q7`, `q8`, `q9`, `q10`, `q11`, `q12`, `q13`, `q14`, `q15`, `q16`, `q17`, `q18`, `q19`, `q20`, `q21`, `q22`, `q23`, `q24`, `q25`, `q26`, `q27`, `q28`, `q29`, `q30`, `q31`.
- `P_OUTPUT_LEVELS`: restore: Each q bit uses 0 V for logic low and vdd for logic high with finite transition smoothing. Required traces: `time`, `q0`, `q1`, `q2`, `q3`, `q4`, `q5`, `q6`, `q7`, `q8`, `q9`, `q10`, `q11`, `q12`, `q13`, `q14`, `q15`, `q16`, `q17`, `q18`, `q19`, `q20`, `q21`, `q22`, `q23`, `q24`, `q25`, `q26`, `q27`, `q28`, `q29`, `q30`, `q31`.

## Modeling Constraints

- AMS role: static trim/configuration bus enable gate for calibration and mode-control flows, not a clocked storage latch.
- Use deterministic combinational voltage-domain enable gating.
- Preserve one-to-one bit alignment across the 32-bit buses.
- Do not add a clock, retained state, undeclared artifacts, debug outputs, validation hooks, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `config_latch_32b.va`.
Every supplied `.va` file is editable; do not add or omit files.
