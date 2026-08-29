# Shared Harbor Environment

This directory is the canonical, task-agnostic agent environment for vaBench.
It intentionally contains only the Docker build inputs needed by the agent:

```text
environment/
├── Dockerfile
├── evaluator-contract.json
├── requirements.in
├── requirements.lock
└── runtime/
    └── entrypoint.sh
```

It must not contain benchmark tasks, hidden tests, checkers, gold solutions,
mutations, evaluator code, credentials, or generated simulation artifacts.

`evaluator-contract.json` is the machine-readable contract for the shared
runtime: Python 3.11.13, hash-locked `evas-sim==0.8.7`, EVAS Rust core identity
(`evas-rust`, ABI `20260718`, core `0.2.4`), public model mounts, hidden-scoring
inputs, and claim boundaries.

The runtime can be built and verified with:

```bash
python3 scripts/verify_evaluator_environment.py --json
benchmark-vabench-release-v4/public-agent-runtime/build.sh
benchmark-vabench-release-v4/public-agent-runtime/verify.sh
```

Harbor task materialization should copy this directory as
`<task>/environment/`, or point at an immutable image built from it. This is a
single shared source; task-specific Dockerfile copies are generated artifacts,
not independently maintained files.
