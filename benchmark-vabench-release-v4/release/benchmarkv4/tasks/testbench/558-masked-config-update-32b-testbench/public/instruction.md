# Masked Config Update 32b Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Masked Config Update 32b` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `masked_config_update_32b.va`:
  - Module `masked_config_update_32b` (entry)
    - position 0: `old_cfg[31]` (input, electrical)
    - position 1: `old_cfg[30]` (input, electrical)
    - position 2: `old_cfg[29]` (input, electrical)
    - position 3: `old_cfg[28]` (input, electrical)
    - position 4: `old_cfg[27]` (input, electrical)
    - position 5: `old_cfg[26]` (input, electrical)
    - position 6: `old_cfg[25]` (input, electrical)
    - position 7: `old_cfg[24]` (input, electrical)
    - position 8: `old_cfg[23]` (input, electrical)
    - position 9: `old_cfg[22]` (input, electrical)
    - position 10: `old_cfg[21]` (input, electrical)
    - position 11: `old_cfg[20]` (input, electrical)
    - position 12: `old_cfg[19]` (input, electrical)
    - position 13: `old_cfg[18]` (input, electrical)
    - position 14: `old_cfg[17]` (input, electrical)
    - position 15: `old_cfg[16]` (input, electrical)
    - position 16: `old_cfg[15]` (input, electrical)
    - position 17: `old_cfg[14]` (input, electrical)
    - position 18: `old_cfg[13]` (input, electrical)
    - position 19: `old_cfg[12]` (input, electrical)
    - position 20: `old_cfg[11]` (input, electrical)
    - position 21: `old_cfg[10]` (input, electrical)
    - position 22: `old_cfg[9]` (input, electrical)
    - position 23: `old_cfg[8]` (input, electrical)
    - position 24: `old_cfg[7]` (input, electrical)
    - position 25: `old_cfg[6]` (input, electrical)
    - position 26: `old_cfg[5]` (input, electrical)
    - position 27: `old_cfg[4]` (input, electrical)
    - position 28: `old_cfg[3]` (input, electrical)
    - position 29: `old_cfg[2]` (input, electrical)
    - position 30: `old_cfg[1]` (input, electrical)
    - position 31: `old_cfg[0]` (input, electrical)
    - position 32: `new_cfg[31]` (input, electrical)
    - position 33: `new_cfg[30]` (input, electrical)
    - position 34: `new_cfg[29]` (input, electrical)
    - position 35: `new_cfg[28]` (input, electrical)
    - position 36: `new_cfg[27]` (input, electrical)
    - position 37: `new_cfg[26]` (input, electrical)
    - position 38: `new_cfg[25]` (input, electrical)
    - position 39: `new_cfg[24]` (input, electrical)
    - position 40: `new_cfg[23]` (input, electrical)
    - position 41: `new_cfg[22]` (input, electrical)
    - position 42: `new_cfg[21]` (input, electrical)
    - position 43: `new_cfg[20]` (input, electrical)
    - position 44: `new_cfg[19]` (input, electrical)
    - position 45: `new_cfg[18]` (input, electrical)
    - position 46: `new_cfg[17]` (input, electrical)
    - position 47: `new_cfg[16]` (input, electrical)
    - position 48: `new_cfg[15]` (input, electrical)
    - position 49: `new_cfg[14]` (input, electrical)
    - position 50: `new_cfg[13]` (input, electrical)
    - position 51: `new_cfg[12]` (input, electrical)
    - position 52: `new_cfg[11]` (input, electrical)
    - position 53: `new_cfg[10]` (input, electrical)
    - position 54: `new_cfg[9]` (input, electrical)
    - position 55: `new_cfg[8]` (input, electrical)
    - position 56: `new_cfg[7]` (input, electrical)
    - position 57: `new_cfg[6]` (input, electrical)
    - position 58: `new_cfg[5]` (input, electrical)
    - position 59: `new_cfg[4]` (input, electrical)
    - position 60: `new_cfg[3]` (input, electrical)
    - position 61: `new_cfg[2]` (input, electrical)
    - position 62: `new_cfg[1]` (input, electrical)
    - position 63: `new_cfg[0]` (input, electrical)
    - position 64: `mask[31]` (input, electrical)
    - position 65: `mask[30]` (input, electrical)
    - position 66: `mask[29]` (input, electrical)
    - position 67: `mask[28]` (input, electrical)
    - position 68: `mask[27]` (input, electrical)
    - position 69: `mask[26]` (input, electrical)
    - position 70: `mask[25]` (input, electrical)
    - position 71: `mask[24]` (input, electrical)
    - position 72: `mask[23]` (input, electrical)
    - position 73: `mask[22]` (input, electrical)
    - position 74: `mask[21]` (input, electrical)
    - position 75: `mask[20]` (input, electrical)
    - position 76: `mask[19]` (input, electrical)
    - position 77: `mask[18]` (input, electrical)
    - position 78: `mask[17]` (input, electrical)
    - position 79: `mask[16]` (input, electrical)
    - position 80: `mask[15]` (input, electrical)
    - position 81: `mask[14]` (input, electrical)
    - position 82: `mask[13]` (input, electrical)
    - position 83: `mask[12]` (input, electrical)
    - position 84: `mask[11]` (input, electrical)
    - position 85: `mask[10]` (input, electrical)
    - position 86: `mask[9]` (input, electrical)
    - position 87: `mask[8]` (input, electrical)
    - position 88: `mask[7]` (input, electrical)
    - position 89: `mask[6]` (input, electrical)
    - position 90: `mask[5]` (input, electrical)
    - position 91: `mask[4]` (input, electrical)
    - position 92: `mask[3]` (input, electrical)
    - position 93: `mask[2]` (input, electrical)
    - position 94: `mask[1]` (input, electrical)
    - position 95: `mask[0]` (input, electrical)
    - position 96: `out_cfg[31]` (output, electrical)
    - position 97: `out_cfg[30]` (output, electrical)
    - position 98: `out_cfg[29]` (output, electrical)
    - position 99: `out_cfg[28]` (output, electrical)
    - position 100: `out_cfg[27]` (output, electrical)
    - position 101: `out_cfg[26]` (output, electrical)
    - position 102: `out_cfg[25]` (output, electrical)
    - position 103: `out_cfg[24]` (output, electrical)
    - position 104: `out_cfg[23]` (output, electrical)
    - position 105: `out_cfg[22]` (output, electrical)
    - position 106: `out_cfg[21]` (output, electrical)
    - position 107: `out_cfg[20]` (output, electrical)
    - position 108: `out_cfg[19]` (output, electrical)
    - position 109: `out_cfg[18]` (output, electrical)
    - position 110: `out_cfg[17]` (output, electrical)
    - position 111: `out_cfg[16]` (output, electrical)
    - position 112: `out_cfg[15]` (output, electrical)
    - position 113: `out_cfg[14]` (output, electrical)
    - position 114: `out_cfg[13]` (output, electrical)
    - position 115: `out_cfg[12]` (output, electrical)
    - position 116: `out_cfg[11]` (output, electrical)
    - position 117: `out_cfg[10]` (output, electrical)
    - position 118: `out_cfg[9]` (output, electrical)
    - position 119: `out_cfg[8]` (output, electrical)
    - position 120: `out_cfg[7]` (output, electrical)
    - position 121: `out_cfg[6]` (output, electrical)
    - position 122: `out_cfg[5]` (output, electrical)
    - position 123: `out_cfg[4]` (output, electrical)
    - position 124: `out_cfg[3]` (output, electrical)
    - position 125: `out_cfg[2]` (output, electrical)
    - position 126: `out_cfg[1]` (output, electrical)
    - position 127: `out_cfg[0]` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `masked_config_update_32b` as `XDUT` with ordered public binding: old_cfg[31]=old_cfg31, old_cfg[30]=old_cfg30, old_cfg[29]=old_cfg29, old_cfg[28]=old_cfg28, old_cfg[27]=old_cfg27, old_cfg[26]=old_cfg26, old_cfg[25]=old_cfg25, old_cfg[24]=old_cfg24, old_cfg[23]=old_cfg23, old_cfg[22]=old_cfg22, old_cfg[21]=old_cfg21, old_cfg[20]=old_cfg20, old_cfg[19]=old_cfg19, old_cfg[18]=old_cfg18, old_cfg[17]=old_cfg17, old_cfg[16]=old_cfg16, old_cfg[15]=old_cfg15, old_cfg[14]=old_cfg14, old_cfg[13]=old_cfg13, old_cfg[12]=old_cfg12, old_cfg[11]=old_cfg11, old_cfg[10]=old_cfg10, old_cfg[9]=old_cfg9, old_cfg[8]=old_cfg8, old_cfg[7]=old_cfg7, old_cfg[6]=old_cfg6, old_cfg[5]=old_cfg5, old_cfg[4]=old_cfg4, old_cfg[3]=old_cfg3, old_cfg[2]=old_cfg2, old_cfg[1]=old_cfg1, old_cfg[0]=old_cfg0, new_cfg[31]=new_cfg31, new_cfg[30]=new_cfg30, new_cfg[29]=new_cfg29, new_cfg[28]=new_cfg28, new_cfg[27]=new_cfg27, new_cfg[26]=new_cfg26, new_cfg[25]=new_cfg25, new_cfg[24]=new_cfg24, new_cfg[23]=new_cfg23, new_cfg[22]=new_cfg22, new_cfg[21]=new_cfg21, new_cfg[20]=new_cfg20, new_cfg[19]=new_cfg19, new_cfg[18]=new_cfg18, new_cfg[17]=new_cfg17, new_cfg[16]=new_cfg16, new_cfg[15]=new_cfg15, new_cfg[14]=new_cfg14, new_cfg[13]=new_cfg13, new_cfg[12]=new_cfg12, new_cfg[11]=new_cfg11, new_cfg[10]=new_cfg10, new_cfg[9]=new_cfg9, new_cfg[8]=new_cfg8, new_cfg[7]=new_cfg7, new_cfg[6]=new_cfg6, new_cfg[5]=new_cfg5, new_cfg[4]=new_cfg4, new_cfg[3]=new_cfg3, new_cfg[2]=new_cfg2, new_cfg[1]=new_cfg1, new_cfg[0]=new_cfg0, mask[31]=mask31, mask[30]=mask30, mask[29]=mask29, mask[28]=mask28, mask[27]=mask27, mask[26]=mask26, mask[25]=mask25, mask[24]=mask24, mask[23]=mask23, mask[22]=mask22, mask[21]=mask21, mask[20]=mask20, mask[19]=mask19, mask[18]=mask18, mask[17]=mask17, mask[16]=mask16, mask[15]=mask15, mask[14]=mask14, mask[13]=mask13, mask[12]=mask12, mask[11]=mask11, mask[10]=mask10, mask[9]=mask9, mask[8]=mask8, mask[7]=mask7, mask[6]=mask6, mask[5]=mask5, mask[4]=mask4, mask[3]=mask3, mask[2]=mask2, mask[1]=mask1, mask[0]=mask0, out_cfg[31]=out_cfg31, out_cfg[30]=out_cfg30, out_cfg[29]=out_cfg29, out_cfg[28]=out_cfg28, out_cfg[27]=out_cfg27, out_cfg[26]=out_cfg26, out_cfg[25]=out_cfg25, out_cfg[24]=out_cfg24, out_cfg[23]=out_cfg23, out_cfg[22]=out_cfg22, out_cfg[21]=out_cfg21, out_cfg[20]=out_cfg20, out_cfg[19]=out_cfg19, out_cfg[18]=out_cfg18, out_cfg[17]=out_cfg17, out_cfg[16]=out_cfg16, out_cfg[15]=out_cfg15, out_cfg[14]=out_cfg14, out_cfg[13]=out_cfg13, out_cfg[12]=out_cfg12, out_cfg[11]=out_cfg11, out_cfg[10]=out_cfg10, out_cfg[9]=out_cfg9, out_cfg[8]=out_cfg8, out_cfg[7]=out_cfg7, out_cfg[6]=out_cfg6, out_cfg[5]=out_cfg5, out_cfg[4]=out_cfg4, out_cfg[3]=out_cfg3, out_cfg[2]=out_cfg2, out_cfg[1]=out_cfg1, out_cfg[0]=out_cfg0.

## Public Parameter Contract

- `masked_config_update_32b.vdd` defaults to `0.9` V; valid range: vdd > 0; sets the voltage-coded output high level.
- `masked_config_update_32b.vth` defaults to `0.45` V; valid range: 0 < vth < vdd; sets the decision threshold for configuration and mask inputs.
- `masked_config_update_32b.tr` defaults to `2e-11` s; valid range: tr > 0; sets output transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_MASKED_SELECTION`: exercise and make observable: For each bit N, out_cfg[N] equals new_cfg[N] when mask[N] is high and equals old_cfg[N] when mask[N] is low. Required traces: `time`, `old0`, `old1`, `old2`, `old3`, `old4`, `old5`, `old6`, `old7`, `old8`, `old9`, `old10`, `old11`, `old12`, `old13`, `old14`, `old15`, `old16`, `old17`, `old18`, `old19`, `old20`, `old21`, `old22`, `old23`, `old24`, `old25`, `old26`, `old27`, `old28`, `old29`, `old30`, `old31`, `new0`, `new1`, `new2`, `new3`, `new4`, `new5`, `new6`, `new7`, `new8`, `new9`, `new10`, `new11`, `new12`, `new13`, `new14`, `new15`, `new16`, `new17`, `new18`, `new19`, `new20`, `new21`, `new22`, `new23`, `new24`, `new25`, `new26`, `new27`, `new28`, `new29`, `new30`, `new31`, `mask0`, `mask1`, `mask2`, `mask3`, `mask4`, `mask5`, `mask6`, `mask7`, `mask8`, `mask9`, `mask10`, `mask11`, `mask12`, `mask13`, `mask14`, `mask15`, `mask16`, `mask17`, `mask18`, `mask19`, `mask20`, `mask21`, `mask22`, `mask23`, `mask24`, `mask25`, `mask26`, `mask27`, `mask28`, `mask29`, `mask30`, `mask31`, `out0`, `out1`, `out2`, `out3`, `out4`, `out5`, `out6`, `out7`, `out8`, `out9`, `out10`, `out11`, `out12`, `out13`, `out14`, `out15`, `out16`, `out17`, `out18`, `out19`, `out20`, `out21`, `out22`, `out23`, `out24`, `out25`, `out26`, `out27`, `out28`, `out29`, `out30`, `out31`.
- `P_ZERO_MASK_IDENTITY`: exercise and make observable: With every mask bit low, the complete output word equals old_cfg. Required traces: `time`, `old0`, `old1`, `old2`, `old3`, `old4`, `old5`, `old6`, `old7`, `old8`, `old9`, `old10`, `old11`, `old12`, `old13`, `old14`, `old15`, `old16`, `old17`, `old18`, `old19`, `old20`, `old21`, `old22`, `old23`, `old24`, `old25`, `old26`, `old27`, `old28`, `old29`, `old30`, `old31`, `mask0`, `mask1`, `mask2`, `mask3`, `mask4`, `mask5`, `mask6`, `mask7`, `mask8`, `mask9`, `mask10`, `mask11`, `mask12`, `mask13`, `mask14`, `mask15`, `mask16`, `mask17`, `mask18`, `mask19`, `mask20`, `mask21`, `mask22`, `mask23`, `mask24`, `mask25`, `mask26`, `mask27`, `mask28`, `mask29`, `mask30`, `mask31`, `out0`, `out1`, `out2`, `out3`, `out4`, `out5`, `out6`, `out7`, `out8`, `out9`, `out10`, `out11`, `out12`, `out13`, `out14`, `out15`, `out16`, `out17`, `out18`, `out19`, `out20`, `out21`, `out22`, `out23`, `out24`, `out25`, `out26`, `out27`, `out28`, `out29`, `out30`, `out31`.
- `P_FULL_MASK_REPLACEMENT`: exercise and make observable: With every mask bit high, the complete output word equals new_cfg. Required traces: `time`, `new0`, `new1`, `new2`, `new3`, `new4`, `new5`, `new6`, `new7`, `new8`, `new9`, `new10`, `new11`, `new12`, `new13`, `new14`, `new15`, `new16`, `new17`, `new18`, `new19`, `new20`, `new21`, `new22`, `new23`, `new24`, `new25`, `new26`, `new27`, `new28`, `new29`, `new30`, `new31`, `mask0`, `mask1`, `mask2`, `mask3`, `mask4`, `mask5`, `mask6`, `mask7`, `mask8`, `mask9`, `mask10`, `mask11`, `mask12`, `mask13`, `mask14`, `mask15`, `mask16`, `mask17`, `mask18`, `mask19`, `mask20`, `mask21`, `mask22`, `mask23`, `mask24`, `mask25`, `mask26`, `mask27`, `mask28`, `mask29`, `mask30`, `mask31`, `out0`, `out1`, `out2`, `out3`, `out4`, `out5`, `out6`, `out7`, `out8`, `out9`, `out10`, `out11`, `out12`, `out13`, `out14`, `out15`, `out16`, `out17`, `out18`, `out19`, `out20`, `out21`, `out22`, `out23`, `out24`, `out25`, `out26`, `out27`, `out28`, `out29`, `out30`, `out31`.
- `P_BIT_INDEPENDENCE`: exercise and make observable: Changing mask or data bit N affects only out_cfg[N]; bus indices are neither reversed nor shifted. Required traces: `time`, `old0`, `old1`, `old2`, `old3`, `old4`, `old5`, `old6`, `old7`, `old8`, `old9`, `old10`, `old11`, `old12`, `old13`, `old14`, `old15`, `old16`, `old17`, `old18`, `old19`, `old20`, `old21`, `old22`, `old23`, `old24`, `old25`, `old26`, `old27`, `old28`, `old29`, `old30`, `old31`, `new0`, `new1`, `new2`, `new3`, `new4`, `new5`, `new6`, `new7`, `new8`, `new9`, `new10`, `new11`, `new12`, `new13`, `new14`, `new15`, `new16`, `new17`, `new18`, `new19`, `new20`, `new21`, `new22`, `new23`, `new24`, `new25`, `new26`, `new27`, `new28`, `new29`, `new30`, `new31`, `mask0`, `mask1`, `mask2`, `mask3`, `mask4`, `mask5`, `mask6`, `mask7`, `mask8`, `mask9`, `mask10`, `mask11`, `mask12`, `mask13`, `mask14`, `mask15`, `mask16`, `mask17`, `mask18`, `mask19`, `mask20`, `mask21`, `mask22`, `mask23`, `mask24`, `mask25`, `mask26`, `mask27`, `mask28`, `mask29`, `mask30`, `mask31`, `out0`, `out1`, `out2`, `out3`, `out4`, `out5`, `out6`, `out7`, `out8`, `out9`, `out10`, `out11`, `out12`, `out13`, `out14`, `out15`, `out16`, `out17`, `out18`, `out19`, `out20`, `out21`, `out22`, `out23`, `out24`, `out25`, `out26`, `out27`, `out28`, `out29`, `out30`, `out31`.
- `P_OUTPUT_LEVELS`: exercise and make observable: Each output bit uses 0 V for logic low and vdd for logic high with finite transition smoothing. Required traces: `time`, `out0`, `out1`, `out2`, `out3`, `out4`, `out5`, `out6`, `out7`, `out8`, `out9`, `out10`, `out11`, `out12`, `out13`, `out14`, `out15`, `out16`, `out17`, `out18`, `out19`, `out20`, `out21`, `out22`, `out23`, `out24`, `out25`, `out26`, `out27`, `out28`, `out29`, `out30`, `out31`.

The required trace names are: `time`, `old0`, `old1`, `old2`, `old3`, `old4`, `old5`, `old6`, `old7`, `old8`, `old9`, `old10`, `old11`, `old12`, `old13`, `old14`, `old15`, `old16`, `old17`, `old18`, `old19`, `old20`, `old21`, `old22`, `old23`, `old24`, `old25`, `old26`, `old27`, `old28`, `old29`, `old30`, `old31`, `new0`, `new1`, `new2`, `new3`, `new4`, `new5`, `new6`, `new7`, `new8`, `new9`, `new10`, `new11`, `new12`, `new13`, `new14`, `new15`, `new16`, `new17`, `new18`, `new19`, `new20`, `new21`, `new22`, `new23`, `new24`, `new25`, `new26`, `new27`, `new28`, `new29`, `new30`, `new31`, `mask0`, `mask1`, `mask2`, `mask3`, `mask4`, `mask5`, `mask6`, `mask7`, `mask8`, `mask9`, `mask10`, `mask11`, `mask12`, `mask13`, `mask14`, `mask15`, `mask16`, `mask17`, `mask18`, `mask19`, `mask20`, `mask21`, `mask22`, `mask23`, `mask24`, `mask25`, `mask26`, `mask27`, `mask28`, `mask29`, `mask30`, `mask31`, `out0`, `out1`, `out2`, `out3`, `out4`, `out5`, `out6`, `out7`, `out8`, `out9`, `out10`, `out11`, `out12`, `out13`, `out14`, `out15`, `out16`, `out17`, `out18`, `out19`, `out20`, `out21`, `out22`, `out23`, `out24`, `out25`, `out26`, `out27`, `out28`, `out29`, `out30`, `out31`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
