# Synthetic native training adapter (AA-VAE-062)

Updated: 2026-08-31. Approved overnight queue N3; independent read-only design
audit recommends this leaf. Main retains final review and publication.

Implementation verified: 41 focused exporter/adapter tests pass. Independent
read-only review found no blocker; main added a full input-digest regression.
Projection contains action/observation metadata and hashes, not raw semantic
training targets. Real-data/semantic projection and training remain separate gates.

## Brief and KPI

Add a pure in-memory adapter from explicitly synthetic native event documents
to the existing AA-VAE-059 training-source/export contract. This closes an
engineering seam, not real trajectory export, training or data authorization.
KPI: deterministic SFT and public-reward RL fixtures pass existing export
validation; malformed provenance, lifecycle, visibility, hashes and split
boundaries fail closed. Existing AA-VAE-059 tests remain unchanged and green.

## Interface and limits

- New `project_synthetic_native_trace_to_training_source` consumes event
  documents and explicit synthetic metadata, mode and split declarations.
  No runtime/file/CLI/provider input, network or persistence API.
- Reuse native event/hash/lifecycle validation and `training_export` builders.
  Use normalized assistant actions and public observations; raw provider payloads,
  hidden reasoning and final/trusted/private evidence cannot become targets or
  rewards. Do not silently discard an unsafe event and export the rest.
- Bind projected source provenance to the input trace identity and adapter
  identity. Bounded finite JSON only; unknown event/payload forms reject rather
  than heuristically extracting arbitrary content.
- Preserve assistant loss targets versus environment/context separation. SFT
  positive examples require submitted/non-budget termination. RL reward must be
  separately declared public validation, never derived from final verdict.
- Only `synthetic-training-fixtures-v1`, `synthetic/` tasks and explicit CC0,
  provider/project/exposure declarations already accepted by AA-VAE-059.
  Train/dev/heldout exclusion stays in the existing split gate. Declarations
  and hashes do not prove real-world license or decontamination.

## Vertical acceptance

1. Small native synthetic action/observation trace -> valid SFT source/export;
   deterministic repeated projection; observations are not assistant targets.
2. Public reward -> valid RL export; no final-score reward extraction.
3. Reject real/r53/unknown source and unauthorized license/provider/project.
4. Reject broken chain, duplicate/mismatched IDs, response without request,
   result without action, unsupported payload, private/final/hidden material
   and model reentry after freeze. Explicit bounds cover oversized input.
5. Rebuilt export detects trace/content mutation; old export tests stay green.

## Ownership and stop

One delegated executor may write only
`runners/agent_harness/training_trace_adapter.py` and
`tests/test_agent_harness_training_trace_adapter.py`. No shared export module,
schemas, launcher, scorer, docs, Git, old workspace, r53 or EVAS writes. Main
owns records/CI/review/integration. Report necessary interface changes upward;
do not widen authorization or introduce another training framework. Hand back
unstaged code/tests, RED/GREEN evidence and known limits, then stop writing.
