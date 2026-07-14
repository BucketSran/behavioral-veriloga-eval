# Polynomial Differential VCVS

## Task Contract
Implement the Verilog-A DUT `polynomial_differential_vcvs.va` for a differential voltage-controlled voltage source with polynomial gain and symmetric output limiting.

## Public Verilog-A Interface
Provide `module polynomial_differential_vcvs(inp, inn, outp, outn);` with electrical inputs `inp`, `inn` and electrical outputs `outp`, `outn`.

## Public Parameter Contract
Expose real parameters `vcmo = 1.1`, `a1 = 1`, `a2 = 0`, `a3 = 0`, `a5 = 0`, `a7 = 0`, and `vsat = 10000000`. Testbenches may override these parameters.

## Required Behavior
Use `V(inp, inn)` as the differential input. Build the output half-swing from the odd and even polynomial coefficients through seventh order, divide the polynomial result by two, limit that half-swing to `[-vsat, vsat]`, and drive `outp` and `outn` symmetrically around `vcmo`.

## Modeling Constraints
Use direct voltage-domain real arithmetic. Preserve differential polarity, the half-swing split, output common mode, and saturation behavior; do not specialize the model to a particular stimulus waveform.

## Output Contract
Submit only the completed Verilog-A module in `polynomial_differential_vcvs.va`.
