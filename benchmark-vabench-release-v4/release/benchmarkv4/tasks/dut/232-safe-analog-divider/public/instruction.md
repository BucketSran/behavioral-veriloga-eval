# Safe Analog Divider

## Task Contract

Implement `safe_analog_divider.va` as an analog divider with a sign-preserving minimum denominator magnitude.

## Public Verilog-A Interface

Use this module signature:

```verilog
module safe_analog_divider(signumer, sigdenom, sigout);
```

All ports are scalar `electrical` nodes. `signumer` is the numerator input, `sigdenom` is the denominator input, and `sigout` is the divided output.

## Public Parameter Contract

- `gain`: multiplier applied to the divided result, default `1.0`.
- `min_sigdenom`: minimum denominator magnitude, default `0.2`.

## Required Behavior

- Use `V(sigdenom)` directly when its magnitude is at least `min_sigdenom`.
- When `V(sigdenom)` is positive but smaller than `min_sigdenom`, use `+min_sigdenom`.
- When `V(sigdenom)` is exactly zero, use `+min_sigdenom`.
- When `V(sigdenom)` is negative but its magnitude is smaller than `min_sigdenom`, use `-min_sigdenom`.
- Drive `sigout` to `gain * V(signumer) / guarded_denominator`.

## Modeling Constraints

Use continuous voltage-domain arithmetic. Preserve denominator sign under the guard, keep the gain parameter active, and do not depend on private stimulus timing or checker-only hooks.

## Output Contract

Return exactly one source artifact named `safe_analog_divider.va`.
