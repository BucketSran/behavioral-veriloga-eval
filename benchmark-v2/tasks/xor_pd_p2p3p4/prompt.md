Write a Verilog-A module named `edge_event_comparator`.

# Task: xor_pd_p2p3p4

## Objective

Create a behavioral model that compares the timing relationship between two event
inputs and produces an output whose average level encodes the offset between them.

## Specification

- **Module name**: `edge_event_comparator`
- **Ports** (all `electrical`, exactly as named):
  `supply_hi`, `supply_lo`, `sig_a`, `sig_b`, `match_out`
- **Parameters**: `vth` (real, default 0.45), `tedge` (real, default 50p)
- **Behavior**:
  - `match_out` is HIGH when `sig_a` and `sig_b` are at **different** logic levels.
  - The module updates its output on every edge (both rising and falling) of
    both `sig_a` and `sig_b`.
  - The fraction of time `match_out` spends high indicates how much the two input
    events are offset in time.
  - Output HIGH = V(supply_hi), LOW = V(supply_lo) — read dynamically from the
    supply ports.
- **Output**: use `transition()` only. No `idt`, `ddt`, or `I() <+`.

Constraints:

- This is NOT a Phase-Frequency Detector (PFD) — do NOT implement UP/DN pulse
  logic with reset feedback.
- This is NOT a Bang-Bang Phase Detector — do NOT sample with a clock or use
  flip-flop based state machines.
- The output is a single continuous signal, not separate UP and DN indicators.

## Testbench requirements

Create a minimal Spectre testbench that:
- Includes `edge_event_comparator.va` via `ahdl_include`
- Provides supply_hi=0.9V, supply_lo=0V
- Generates two periodic signals (sig_a and sig_b) with a phase offset
- Saves signals: `sig_a`, `sig_b`, `match_out`
- Runs transient for ~200ns

## Deliverable

Two files:
1. `edge_event_comparator.va` - the Verilog-A behavioral model
2. `tb_edge_event_comparator.scs` - the Spectre testbench

Expected behavior:
- Output is high when inputs differ, low when they match
- Average output voltage reflects the relative timing offset between sig_a and sig_b

Ports:
- `SUPPLY_HI`: inout electrical
- `SUPPLY_LO`: inout electrical
- `SIG_A`: input electrical
- `SIG_B`: input electrical
- `MATCH_OUT`: output electrical

## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the
generated artifact. It does not prescribe the internal implementation or reveal
a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=200n maxstep=100p errpreset=conservative
```

Required public waveform columns in `tran.csv`:

- `sig_a`, `sig_b`, `match_out`

Use plain scalar save names for these observables; do not rely on
instance-qualified or aliased save names.

Timing/checking-window contract:

- Both `sig_a` and `sig_b` must provide enough valid edges for the checker to
  sample settled outputs.
- Sequential outputs are sampled shortly after input edges, so drive outputs
  with stable held state variables and `transition()` targets.
- Public stimulus nodes used by the reference harness include: `supply_hi`,
  `supply_lo`, `sig_a`, `sig_b`.
