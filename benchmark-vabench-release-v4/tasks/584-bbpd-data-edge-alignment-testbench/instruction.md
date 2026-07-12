# BBPD Data Edge Alignment Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `BBPD Data Edge Alignment` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `bbpd_data_edge_alignment_ref.va`:
  - Module `bbpd_data_edge_alignment_ref` (entry)
    - position 0: `vdd` (inout, electrical)
    - position 1: `vss` (inout, electrical)
    - position 2: `clk` (input, electrical)
    - position 3: `data` (input, electrical)
    - position 4: `up` (output, electrical)
    - position 5: `dn` (output, electrical)
    - position 6: `retimed_data` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `bbpd_data_edge_alignment_ref` as `XDUT` with ordered public binding: vdd=vdd, vss=vss, clk=clk, data=data, up=up, dn=dn, retimed_data=retimed_data.

## Public Parameter Contract

- `bbpd_data_edge_alignment_ref.vth` defaults to `0.45` V; valid range: finite real within the vss-to-vdd logic range; sets clk and data logic thresholds relative to vss.
- `bbpd_data_edge_alignment_ref.trf` defaults to `3e-11` s; valid range: trf > 0; sets output transition smoothing.
- `bbpd_data_edge_alignment_ref.clk_period` defaults to `2e-08` s; valid range: clk_period > 0; sets nominal full clock period for transition timing classification.
- `bbpd_data_edge_alignment_ref.clk_delay` defaults to `1e-08` s; valid range: clk_delay >= 0; sets initial nominal clock phase reference.
- `bbpd_data_edge_alignment_ref.deadzone` defaults to `8e-10` s; valid range: deadzone >= 0; sets the edge-centered pulse-suppression region.
- `bbpd_data_edge_alignment_ref.pulse_w` defaults to `1e-09` s; valid range: pulse_w > 0; sets UP or DN correction-pulse width.
- `bbpd_data_edge_alignment_ref.poll_dt` defaults to `5e-11` s; valid range: poll_dt > 0; sets pulse-expiration polling cadence.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_CLOCKED_RETIMING`: exercise and make observable: Each rising clk edge captures the current data logic level onto retimed_data, which holds between clock edges. Required traces: `time`, `clk`, `data`, `retimed_data`.
- `P_EARLY_TRANSITION_UP`: exercise and make observable: A data transition closer to the upcoming nominal clock edge and outside the deadzone produces an UP pulse of pulse_w duration. Required traces: `time`, `clk`, `data`, `up`, `dn`.
- `P_LATE_TRANSITION_DN`: exercise and make observable: A data transition closer to the previous nominal clock edge and outside the deadzone produces a DN pulse of pulse_w duration. Required traces: `time`, `clk`, `data`, `up`, `dn`.
- `P_DEADZONE_SUPPRESSION`: exercise and make observable: Data transitions within deadzone of the relevant nominal clock edge produce neither correction pulse. Required traces: `time`, `clk`, `data`, `up`, `dn`.
- `P_BOTH_DATA_POLARITIES`: exercise and make observable: Both rising and falling data transitions participate in timing classification. Required traces: `time`, `clk`, `data`, `up`, `dn`.
- `P_MUTUAL_EXCLUSION`: exercise and make observable: UP and DN are mutually exclusive apart from finite analog transition overlap and use the vdd-to-vss logic range. Required traces: `time`, `vdd`, `vss`, `up`, `dn`.

The required trace names are: `time`, `vdd`, `vss`, `clk`, `data`, `up`, `dn`, `retimed_data`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
