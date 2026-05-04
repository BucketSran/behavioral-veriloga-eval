# module_header_backslash_continuation

## Trigger

Use this skill when strict preflight reports `spectre_strict:module_header_backslash_continuation` or real Spectre reports `VACOMP-2259` on a Verilog-A module declaration line that contains a trailing `\`.

## Rule

Backslash continuation is Spectre testbench syntax, not Verilog-A module-header syntax. A Verilog-A header may span multiple physical lines without `\` characters:

```verilog-a
module dut (in, out,
            vdd, vss);
```

Do not write:

```verilog-a
module dut (in, out, \
            vdd, vss);
```

## Repair Pattern

Remove only the trailing `\` characters inside the `module ... (...);` header. Preserve the module name, port order, commas, declarations, body, parameters, and behavior.

## Safety Boundary

This is a syntax-only compile skill. It must not rename ports, reorder ports, add or remove ports, change directions, or alter circuit behavior. Accept the edit only through the strict preflight / EVAS / Spectre compile gate.
