# Public Spectre / Verilog-A Compatibility Rules

These rules are public simulator-compatibility constraints. They do not reveal
any checker implementation, gold waveform, task-specific answer, or hidden
benchmark detail.

## Verilog-A Source Files

- Write pure Verilog-A that Cadence Spectre AHDL can compile.
- Include `constants.vams` and `disciplines.vams`.
- Use analog behavioral constructs such as `analog begin ... end`, `V(node) <+`,
  `transition`, `@(initial_step)`, `@(final_step)`, `@(timer(...))`,
  `@(cross(...))`, and `@(above(...))`.
- Do not use digital Verilog or SystemVerilog constructs such as `reg`, `wire`,
  `logic`, `always @`, `initial begin`, `assign`, nonblocking assignments,
  packed vectors on integer variables, or Verilog bit literals.
- Prefer the portable non-ANSI Verilog-A declaration style:

```verilog-a
module NAME (in, out, vdd, vss);
    input in;
    output out;
    inout vdd, vss;
    electrical in, out, vdd, vss;
endmodule
```

- If ANSI-style ports are used, keep the declaration fully in the module header.
  Do not write body-level combined direction/discipline declarations such as
  `input electrical vin;` or `output electrical vout;`.
- Declare `integer` and `real` variables before executable statements in a
  block, or at module scope. Do not introduce declarations after assignments,
  conditionals, loops, or contribution statements inside the same block.
- Avoid function-style integer casts such as `integer(x)`. Use integer state
  variables and explicit arithmetic/clamping instead.
- Do not reuse a port or electrical node name as a parameter or local variable.
  For example, if `vdd` is a port, use a parameter name such as `vhi` or
  `vdd_level`, not `parameter real vdd = ...`.
- If random distribution functions are used, declare the seed as an `integer`.
  Do not pass a `real` seed variable to `$rdist_*` or `$dist_*` functions.
- Do not put modulo expressions directly inside array subscripts. Normalize the
  index into a non-negative bounded integer first, then use that integer as the
  array index.
- For file output, open a descriptor with `$fopen` and pass the descriptor to
  `$fstrobe`, `$fwrite`, or `$fdisplay`. Do not pass a filename string directly
  to those functions.
- Keep analog event operators as explicit event controls. Avoid placing
  `cross`, `above`, `transition`, or similar analog operators inside code shapes
  that make them conditionally instantiated.

## Spectre Testbench Files

- Start Spectre netlists with `simulator lang=spectre`; add `global 0` when a
  global ground declaration is needed.
- Include generated Verilog-A files with explicit `ahdl_include "file.va"`
  lines.
- Instantiate Verilog-A modules with Spectre positional instance syntax, for
  example `XDUT (in out vdd vss) module_name`.
- Instantiate ideal sources with Spectre instance syntax, for example
  `Vclk (clk 0) vsource type=pulse ...` or `Vdd (vdd 0) vsource dc=1.8`.
  Do not write reversed primitive syntax such as `vsource vdd (vdd 0) ...`.
- For `type=pulse` sources, use strictly positive rise and fall times. Do not
  set `rise=0` or `fall=0`.
- For `type=pwl` sources, list time/value pairs with strictly increasing time
  entries. Do not encode ideal steps with duplicate timestamps.
- Long instance node lists must either stay on one line or use explicit `\`
  line continuation. Do not split `XDUT (...) module_name` across bare lines.
- Do not use Verilog named-port instance syntax inside `.scs` files.
- Do not use brace blocks such as `{ ... }` in Spectre netlists.
- Avoid single-quoted expressions such as `width='period/2'`. Use plain numeric
  values or Spectre-compatible parameter expressions.
- Do not drive the same node pair with multiple ideal `vsource` elements.
  Combine DC, pulse, or PWL stimulus for a node into one source.
- Save public scalar waveform names plainly when possible. Avoid relying on
  simulator-specific hierarchical or colon-qualified save names unless the task
  explicitly requires them.

## Output Discipline

- Return only the required fenced code blocks.
- If both a DUT and a testbench are required, output the DUT block first and the
  Spectre testbench block second.
- Do not add explanatory prose outside the code blocks.
