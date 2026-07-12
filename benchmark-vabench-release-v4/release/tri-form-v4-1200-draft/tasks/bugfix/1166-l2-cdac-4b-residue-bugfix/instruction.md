# L2 CDAC 4b Residue Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `l2_cdac_4b_residue.va`:
  - Module `l2_cdac_4b_residue` (entry)
    - position 0: `vin` (input, electrical)
    - position 1: `clks` (input, electrical)
    - position 2: `dctrl1` (input, electrical)
    - position 3: `dctrl2` (input, electrical)
    - position 4: `dctrl3` (input, electrical)
    - position 5: `vres` (output, electrical)

## Public Parameter Contract

- `l2_cdac_4b_residue.vdd` defaults to `1`; valid range: finite; overrides vdd.
- `l2_cdac_4b_residue.vrefp` defaults to `1`; valid range: finite; overrides vrefp.
- `l2_cdac_4b_residue.vrefn` defaults to `0`; valid range: finite; overrides vrefn.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_FALLING_CLOCK_SAMPLE`: restore: `vin` is sampled into the residue on initial step and on falling `clks` crossings through `vdd/2`. Required traces: `time`, `vin`, `clks`, `vres`.
- `P_CONTROL_STEP_WEIGHTS`: restore: Rising control crossings add positive capacitive reference steps: `dctrl3` is half scale, `dctrl2` quarter scale, and `dctrl1` eighth scale. Required traces: `time`, `dctrl1`, `dctrl2`, `dctrl3`, `vres`.
- `P_RETAINED_RESIDUE_OUTPUT`: restore: `vres` retains the accumulated sampled residue between clock/control events. Required traces: `time`, `vin`, `clks`, `dctrl1`, `dctrl2`, `dctrl3`, `vres`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `l2_cdac_4b_residue.va`.
Every supplied `.va` file is editable; do not add or omit files.
