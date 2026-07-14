# Latched Comparator Delay

## Task Contract

Implement the requested Verilog-A artifact for `Latched Comparator Delay`.
- Form: `dut`
- Level: `L1`
- Category: `data_converter`
- Target artifact(s): `latched_comparator_delay.va`

Implement `latched_comparator_delay.va` in Verilog-A as a converter front-end
interface primitive: a differential analog input is sampled by a latch clock and
published as a supply-referenced voltage-coded decision.

## Public Verilog-A Interface

Declare module `latched_comparator_delay(DOUT, GND, VDD, CLK, VINN, VINP)` with
scalar electrical voltage-domain ports. `GND` and `VDD` are the output rail
references, `CLK` is the latch clock, `VINP`/`VINN` are the differential analog
input pair, and `DOUT` is the voltage-coded latched decision that bridges the
analog comparison into the converter readout path.

## Public Parameter Contract

Provide these overrideable public parameters:

- `td = 1n`: output delay after a latch event.
- `tr = 100p`: output transition smoothing time.
- `vos = 0`: deterministic input-referred offset.
- `vn = 1m`: standard deviation of the input-referred random decision term.
- `seed_init = 0`: seed used to initialize the random decision sequence.

## Required Behavior

- At `initial_step`, derive `vh`, `vl`, and the clock threshold from `VDD` and
  `GND`, and initialize the random seed from `seed_init`.
- On each rising crossing of `CLK` through the midpoint of the supply rails,
  latch whether `VINP - VINN` exceeds `vos` plus the random decision term.
- When `vn` is zero, the random term is deterministic zero; when `vn` is
  nonzero, draw it from a normal distribution using the initialized seed.
- Hold the latched value between clock events.
- Drive `DOUT` to the derived supply rails with the configured delay and
  transition time.

## Modeling Constraints

Return only `latched_comparator_delay.va`. Do not emit a testbench,
validation logic, validation-only hooks, or simulator-specific side channels. Use
voltage contributions only; do not use current contributions, `ddt()`, or
`idt()`.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `latched_comparator_delay.va`. Do not include explanatory prose outside the source artifact contents.
