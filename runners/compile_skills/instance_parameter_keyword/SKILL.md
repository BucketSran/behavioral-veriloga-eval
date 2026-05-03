# instance_parameter_keyword

## Trigger

Use this skill when EVAS/Spectre-strict reports `spectre_strict:instance_parameters_keyword`.

## Rule

The generated Spectre instance line should pass parameter assignments directly after the model name. The extra keyword `parameters` is not accepted in this context.

## Repair Pattern

```spectre
XDUT (in out) my_model parameters gain=2
```

becomes:

```spectre
XDUT (in out) my_model gain=2
```

For continued multi-line instances, remove only the continuation keyword and
preserve assignments:

```spectre
XDUT (clk rst \
      out) my_model \
      parameters vdd=vdd vth=vth
```

becomes:

```spectre
XDUT (clk rst \
      out) my_model \
      vdd=vdd vth=vth
```

## Safety Boundary

Do not change node order, model name, or assignment values.
