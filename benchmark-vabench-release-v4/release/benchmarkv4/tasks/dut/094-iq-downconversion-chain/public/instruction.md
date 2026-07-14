# IQ Downconversion Chain

## Task Contract

Implement the requested Verilog-A artifact for `IQ Downconversion Chain`.
- Form: `dut`
- Level: `L2`
- Category: `rf_afe_behavioral_macromodels`
- Target artifact(s): `iq_downconversion_chain.va`

Implement a voltage-domain I/Q downconversion receiver macromodel.

## Public Verilog-A Interface

Declare module `iq_downconversion_chain` with positional ports `clk, rst, vin,
out, metric, lo_i, lo_q, mix_i, mix_q, phase_mon`. All ports are electrical.

`clk` advances the quadrature LO phase, `rst` is an active-high voltage-coded
reset, `vin` is the RF input envelope centered around common mode, `out` is the
I-path baseband output, `metric` is the Q-path baseband output, `lo_i` and
`lo_q` expose voltage-coded I/Q LO polarity, `mix_i` and `mix_q` expose the
corresponding bounded mixer outputs, and `phase_mon` exposes the quadrature
phase state.

## Public Parameter Contract

Provide these overrideable public parameters:

- `tr = 80p`: transition time used for smoothed voltage contributions.
- `vth = 0.45 V`: threshold for voltage-coded logic decisions.

## Required Behavior

On reset, return the I/Q baseband outputs, LO monitors, and mixer monitors to
the 0.45 V common-mode level. Drive `phase_mon` to 0.9 V on reset and
initialize the phase state so the first post-reset rising `clk` crossing
advances to phase 0.

After reset releases, advance a four-state quadrature LO sequence on each
rising `clk` crossing and wrap from phase 3 back to phase 0. Use this
coefficient table:

| Phase | I coefficient | Q coefficient |
| ---: | ---: | ---: |
| 0 | 1.0 | 0.0 |
| 1 | 0.0 | 1.0 |
| 2 | -1.0 | 0.0 |
| 3 | 0.0 | -1.0 |

For each phase, drive `lo_i` and `lo_q` as
`0.45 V + 0.40 V * coefficient`. Compute each mixer monitor as
`0.45 V + 1.25 * (vin - 0.45 V) * coefficient`, then clamp each mixer monitor
to `[0.02 V, 0.88 V]`.

Update each I/Q baseband state once per valid clock edge using
`state_next = state_prev + 0.85 * (mixer_value - state_prev)`, then clamp the
state to `[0.02 V, 0.88 V]`. Drive `out` from the I-path state and `metric`
from the Q-path state. Drive `phase_mon` as `phase / 3.0 * 0.9 V`.

## Modeling Constraints

Return only `iq_downconversion_chain.va`. Use voltage contributions only. Use
event-updated behavioral state on the clock edge and `transition(...)`
smoothing for output contributions. Do not modify or emit the support
testbench, add validation logic, hard-code specific waveform sample points, add
simulator-specific side channels, use current contributions, transistor-level
devices, S-parameters, AC/noise-analysis behavior, communication modem
algorithms, or full link-level decoding.

Use deterministic Verilog-A behavioral modeling appropriate for the public circuit contract. Do not hard-code validation stimulus tables, transient stop times, or sample windows into the DUT unless that behavior is part of the public circuit contract.

## Output Contract

Return exactly one complete source artifact named `iq_downconversion_chain.va`. Do not include explanatory prose outside the source artifact contents.
