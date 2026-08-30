# Evolution extension and information-surface closure (N4/N5)

2026-08-31. Follow AA-VAE-061–063. Main owns implementation/integration/Git;
independent reviewers advise only. No paid call, real corpus, training, new
dependency, CLI default switch, sealed r53 or EVAS change.

## Ordered test-first slices

1. AA-VAE-064: repair the demonstrated generation export mismatch. Branches
   retain the logical Evolution identity but export an internal copy of the cell
   as Agent-No-EVAS with executable_feedback=false. Public-validation and final
   runtimes remain separately exported using the original cell. Record logical
   versus generation arm in hashed config/branch evidence. Replace only the
   stale NoEVAS wrapper's private-Spectre-judge sentence with frozen trusted
   replay wording; do not remove legitimate Verilog-A/Spectre syntax guidance.
   RED: spy actual branch/public/final export inputs; exported public prompt,
   runtime JSON/access policy; original cell unmodified. Existing real three-form
   Docker Evolution smoke must still validate branches and final-score once.

2. AA-VAE-065: explicit synthetic docs_corpus Python API for Evolution only.
   Reuse OfflineDocsTool, capability registry, _RecordedEnvironment and policy
   provider tools; each branch gets an independent tool wrapper over immutable
   corpus bytes. Bind complete profile plus digest/intervention in config before
   hashing, include profile identity in the task prompt and final evidence.
   Only exact AlphaApollo-Evolution+EVAS may enable this opt-in; no new CLI flags.
   Docs are branch-local reference observations, not new shared-memory records;
   existing sealed prior candidate/public-checker feedback remains the only
   cross-branch projection. Final results never reenter generation. Ordinary
   single-trajectory summary/ledger must reject Evolution/intervention rows.
   RED: two rounds/docs calls, profile identity and budget charges, per-branch
   separation, tamper/condition rejection, explicit nonpooling and no final text
   in model requests/memory. Free scripted-provider Docker smoke plus CI gate.

3. AA-VAE-066: small machine-readable policy disclosure and failure projection.
   Reuse run_campaign for a pure declared-information-surface helper, attached
   before config hashing in native launcher and Evolution config/final report.
   Declare logical/exported arm, Bash/EVAS/coordinate-validation access and
   extension IDs. Explicitly mark this as expected policy, not observed image
   audit/attestation. State installed examples may differ, information parity
   is not established, and shared final feedback is prohibited. Do not claim
   all provider/model or prompt differences are controlled.
   Reuse result_protocol.normalize_failure_taxonomy for Evolution setup/final/
   public-cleanup failures: infrastructure/system with phase recorded separately.
   Unknown no-selected-candidate cause remains undetermined, not blamed on model.
   Successful execution with a failing final judgment must retain its candidate
   verdict, not be relabeled as infrastructure; expose taxonomy only where
   evidence supports it. No automatic retry activation.

## Exact writable files

Main: calibration-pilot run_native_evolution.py, run_campaign.py,
run_native_mini_swe.py, score_campaign.py; offline_docs_tool.py; existing native
Evolution/docs/launcher/campaign/CI tests and new focused
tests/test_agent_harness_evolution_extensions.py; CI, runner README, feature
notes, active plans, ownership and logs. No shared schema/controller changes.
The completed N2/N3 delegated leaves stay closed. Every slice has an independent
read-only review and a separate GREEN commit before dependent integration.

## Stop boundary

N4 closes the currently missing synthetic Evolution docs seam, not real corpus
quality or arbitrary extension rollout. Waveform remains an explicit native
API until its Evolution selection/feedback contract is independently specified;
adding waveform to shared selection without that contract is outside this slice.
Real matched RAG/waveform campaigns, semantic trajectory exports, SFT/RL trainers
and new spending need external data/policy decisions and are recorded as such.
