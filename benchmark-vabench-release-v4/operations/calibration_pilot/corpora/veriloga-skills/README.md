# Pinned Verilog-A reference corpus

This is a ready-to-load reviewed-v2 manifest, not a new retrieval engine.
It uses the existing `OfflineDocsCorpus` and `run_combined_tools.py` docs options.
The project user explicitly authorized source use; see `authorization.md`.
The manifest binds that record's exact SHA-256. It does not grant other projects
a public license. Reference bodies stay local and are not vendored here.

## Acquire and check

From the benchmark repository root, use a fresh ignored directory. These
commands fetch only the four reviewed files at the immutable commit; they do
not clone or execute the upstream skill. Retrieval during a run stays offline.
`curl` downloads the bytes; the existing corpus loader verifies them.

```bash
(
  set -eu
  corpus_root=$(mktemp -d benchmark-vabench-release-v4/reports/veriloga-skills-7c5d3f03-XXXXXX)
  for corpus_file in modules-ports-disciplines analog-contributions events-state-control operators-system-tasks; do
    curl --fail --silent --show-error --location --max-time 45 \
      "https://raw.githubusercontent.com/Arcadia-1/veriloga-skills/7c5d3f03a162ee8131103e9551eee842424360bb/veriloga/references/${corpus_file}.md" \
      -o "$corpus_root/$corpus_file.md"
  done
  VAEVAS_VERILOGA_DOCS_ROOT="$corpus_root" .venv/bin/python -m pytest -q \
    tests/test_agent_harness_veriloga_corpus.py
  printf 'Verified local corpus: %s\n' "$corpus_root"
)
```

An interrupted or wrong-hash download is not an accepted corpus. Use a fresh
directory to retry; never change expected hashes to make a download pass.
CI checks metadata/authorization/contracts using synthetic replacement bodies;
the four real-source tests opt in via the environment variable above and do not
download anything. Without it, their skips are explicit, not real-data evidence.

## Existing harness integration

Pass these two options to the existing combined `prepare` and `run` commands,
alongside their required model/budget/image/output controls:

```text
--docs-root <verified-local-corpus-directory>
--docs-manifest benchmark-vabench-release-v4/operations/calibration_pilot/corpora/veriloga-skills/manifest.json
```

The direct API is unchanged:

```python
import json
from pathlib import Path
from runners.agent_harness.tools.offline_docs import OfflineDocsCorpus

manifest_path = Path("benchmark-vabench-release-v4/operations/calibration_pilot/corpora/veriloga-skills/manifest.json")
corpus = OfflineDocsCorpus.from_manifest(
    Path("<verified-local-corpus-directory>"),
    json.loads(manifest_path.read_text(encoding="utf-8")),
)
corpus.assert_model_context_allowed(external_provider=True)
result = corpus.search("initial_step cross threshold events", top_k=1)
```

Neither loading nor searching calls a model, spends an API budget or modifies
an existing campaign. A new campaign freezes this profile explicitly. The
separate dated provider review and monetary launch controls remain mandatory;
corpus permission is not fee approval. Do not alter old frozen campaigns.

## Review and limits

The four complete files were read at the pinned revision. They contain general
language guidance and generic snippets, not identified benchmark tasks, expected
task answers, checker internals or scored-run feedback. This bounded manual
review does not prove zero overlap with every benchmark. Excluded: evals, tests,
examples, examples-archive, reference categories and EVAS/OpenVAF workflows.

These are authoring references, not the normative language standard or an EVAS
0.8.7 compatibility promise: current/noise/Laplace operators and other constructs
may be outside EVAS's supported subset. Public runtime feedback and frozen task
constraints still govern. Imperative prose and code blocks remain untrusted
reference data, never tool authority or executable setup instructions.

Existing retrieval is English lexical overlap, one chunk per file, and a
600-character **prefix**, not a query-centered excerpt. A match may refer to
material later than the returned prefix. The four smoke queries establish
deterministic source selection only, not full section coverage or improved model
quality. Query-aware chunking would be a separately versioned intervention.

Cadence is omitted: the scoped current/old vaEVAS filename search found no
recognizable manual. No archives were restored and no substitute was downloaded.
