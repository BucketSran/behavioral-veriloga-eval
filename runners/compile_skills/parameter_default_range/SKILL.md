# parameter_default_range

## Trigger

Use this skill when EVAS/Spectre-strict reports either:

- `spectre_strict:parameter_default_range`
- `spectre_strict:parameter_open_upper_range`

## Rule

Spectre rejects parameter declarations whose default value violates the declared
`from (...)` range, even if EVAS could otherwise evaluate the model.

Spectre also rejects empty upper-bound range syntax such as:

```verilog-a
parameter real tr = 1n from (0:);
parameter real td = 0n from [0:);
```

## Repair Pattern

Remove only the incompatible range clause and preserve the generated default value:

```verilog-a
parameter real vlo = 0.0 from (0:inf);
```

becomes:

```verilog-a
parameter real vlo = 0.0;
```

The same repair applies to empty upper-bound syntax:

```verilog-a
parameter real tr = 1n from (0:);
```

becomes:

```verilog-a
parameter real tr = 1n;
```

## Safety Boundary

Do not change the default value. The checker will catch behavior issues caused by the default itself.
