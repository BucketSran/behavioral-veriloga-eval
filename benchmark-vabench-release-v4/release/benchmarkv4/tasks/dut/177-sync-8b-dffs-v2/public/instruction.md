# Synchronous 8-bit DFF Chain V2

## Task Contract

- Form: `dut`.
- Level: `L1`.
- Category: sampled-data alignment/control support.
- Target artifact: `sync_8b_dffs_v2.va`.
- Role: multi-phase nine-bit DFF alignment chain.
- Output boundary: implement only the requested public Verilog-A DUT artifact.

## Public Verilog-A Interface

Declare the public module exactly as:

```verilog
module sync_8b_dffs_v2(ck1, ck2, ck3, ck4, ck5, ck6, ck7, ck8, ck9, dl0, dl1, dl2, dl3, dl4, dl5, dl6, dl7, dl8, do0, do1, do2, do3, do4, do5, do6, do7, do8);
```

`ck1..ck9` are phase clocks, `dl0..dl8` are voltage-coded data inputs, and `do0..do8` are aligned voltage-coded outputs. All ports are electrical.

## Public Parameter Contract

Provide overrideable parameters `vth = 0.45` and `tt = 20p` for clock/input thresholds and output transition shaping.

## Required Behavior

Implement the staged nine-bit alignment chain. Each phase clock captures its corresponding input and shifts previously captured upper-phase data down the chain; `ck9` captures `dl8`, `ck8` shifts that value and captures `dl7`, continuing down to `ck1`. On `ck1`, publish the complete aligned word on `do0..do8`. Hold outputs between publishing events.

## Modeling Constraints

Use deterministic voltage-domain Verilog-A with voltage contributions and event-driven state where needed. Do not add checker logic, hard-code testbench-only sample times, add simulator-private side channels, use transistor-level devices, or introduce current-domain behavior.

## Output Contract

Return exactly one complete Verilog-A source file named `sync_8b_dffs_v2.va`. Do not generate a testbench, checker, waveform postprocessor, companion support module, or explanatory prose outside the requested source artifact.
