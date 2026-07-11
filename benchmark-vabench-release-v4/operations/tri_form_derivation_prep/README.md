# Tri-Form Release Builder

This directory contains the isolated preparation and materialization tools for
deriving the Testbench and Bugfix forms from the 400 canonical DUT families.

It intentionally does not modify:

- `tasks/` or `formal_tasks/`;
- `formal_derivatives/`;
- task-local `evaluator/certification.json` files;
- release manifests or `TOOLCHAIN_LOCK.json`;
- any `operations/task_side_*` closeout directory.

`build_sync_prep.py` is the historical pre-freeze inventory builder.
`materialize_tri_form_release.py` is the release builder: it consumes the
hash-bound exact-five DUT denominator and creates 400 DUT, 400 Testbench, and
400 Bugfix task views plus the G0-G5 experiment records.

The generated plan activates exactly five mutations per family: 2,000 active
mutations in the formal tri-form release. The 51 source-catalog extras remain
in a provenance-only archive index and are not exported as scored cases.

The release treats `evaluator/score_tb.scs` as the canonical reference fixture.
Existing score-profile gold and mutation evidence is reused by hash.
Mutations certified only under a legacy feedback deck enter a cross-profile
audit queue; they are rerun only when semantic witness portability cannot be
proved. Legacy include paths use a content-identical private path adapter and
do not trigger analog reruns by themselves. Public candidate testbenches still
use the canonical `./dut/{artifact_path}` binding.

Materialize and audit the 1,200 task views:

```bash
python3 operations/tri_form_derivation_prep/materialize_tri_form_release.py
python3 operations/tri_form_derivation_prep/audit_tri_form_release.py
```

Export one runtime record without mounting evaluator-private files:

```bash
python3 operations/tri_form_derivation_prep/export_tri_form_runtime.py \
  --task-id v4-501 --mode G2 --output /tmp/vabench-runtime-v4-501-g2
python3 operations/tri_form_derivation_prep/audit_runtime_export.py \
  --bundle /tmp/vabench-runtime-v4-501-g2
```

Rebuild the historical preparation snapshot only when its input inventory is
needed:

```bash
python3 operations/tri_form_derivation_prep/build_sync_prep.py
```

The materialized release is structurally audited, but its status remains
`materialized_gate3_audit_pending`. Runtime export evidence proves record
ingestion and public/private bundle isolation only. It is not a model-run
result, a fixed-toolchain EVAS/Spectre certification, or a final score.

The old `formal_derivatives/` front-20 packages are prototypes and are not the
canonical 800 derivative tasks. The canonical generated views live under
`release/tri-form-v4-1200-draft/tasks/` until the final Gate 3 release name and
toolchain identity are sealed.
