# vaBench Public Agent Runtime

中文操作说明见 [`README.zh-CN.md`](README.zh-CN.md)。

The repository-level [`environment/`](../../environment/) directory is the
single shared Harbor-compatible Docker build source. The helpers in this
directory build and run that public, task-agnostic environment for a Verilog-A
agent with Bash and EVAS. The image contains no benchmark task,
checker, evaluator, gold solution, hidden test, mutation catalog, credential,
or internal registry configuration. One sanitized public task is mounted
read-only at runtime; only the submission and working directories are writable.

## Build

Requirements:

- Docker with Buildx
- public access to Docker Hub and PyPI
- an `amd64` host, or Docker emulation for `linux/amd64`

```bash
git clone https://github.com/Arcadia-1/behavioral-veriloga-eval.git
cd behavioral-veriloga-eval
git checkout <approved-commit>
cd benchmark-vabench-release-v4/public-agent-runtime
./build.sh
```

`environment/requirements.lock` pins EVAS and every Python dependency by
version and SHA-256. `environment/Dockerfile` pins the base image by digest.
`build.sh` creates the matched
`vabench-agent-runtime:0.8.4` and
`vabench-agent-runtime:0.8.4-noexec` images. The latter uses the same base,
lockfile, and shell environment but removes the EVAS package and executable for
the Agent-NoExec control arm. Record both image IDs printed by `build.sh`;
campaign records should use those immutable identities.

## Verify

```bash
./verify.sh
```

The verifier creates bind-mounted scratch directories below this runtime
directory so Docker Desktop and Colima can access them. Set
`VABENCH_DOCKER_SHARED_TMPDIR` to another Docker-shared host directory when
needed.

The verifier checks:

- EVAS 0.8.4 is installed with a loadable Rust core;
- the public task mount is readable but not writable;
- submission and work mounts are writable;
- strict EVAS simulation produces a readable `tran.csv`;
- the matched Agent-NoExec image exposes neither the `evas` command nor its
  Python module;
- the image does not expose `/opt/benchmark` or `/workspace/evaluator`.

## Run One Assigned Task

Prepare three host directories:

```text
task/        sanitized public material for exactly one assigned task
submission/  final candidate artifacts
skills/      optional read-only skill packages for skill-enabled modes
work/        disposable agent working files
```

Then start an interactive shell:

```bash
./run.sh ./task ./submission ./work
```

Or provide an agent command:

```bash
cp /path/to/agent ./work/agent
./run.sh ./task ./submission ./work /workspace/work/agent --workspace /workspace
```

Inside the container, a DUT or bugfix task can be simulated with:

```bash
evas simulate public/task/visible_test.scs \
  -o /tmp/vabench-visible/evas-output \
  --spectre-strict
python3 -c 'import csv; print(next(csv.DictReader(open("/tmp/vabench-visible/evas-output/tran.csv"))))'
```

Testbench tasks use the fixed `candidate_command_template` in
`public/task/evas_runtime.json` for the named public cases.

Skill-enabled benchmark modes may also mount `public/skills/<id>/SKILL.md`
and related reference files. These are read-only, task-agnostic skill packages;
their contents are not part of the task prompt and must not include evaluator,
gold, checker, or hidden-case material.
For manual runs, set `VABENCH_SKILLS_DIR=/path/to/skills` before invoking
`run.sh` to add this optional read-only mount.

## Isolation Contract

The launcher uses a read-only root filesystem, drops Linux capabilities,
enables `no-new-privileges`, disables networking by default, and mounts only:

```text
/workspace/public/task        read-only
/workspace/public/skills      optional read-only
/workspace/public/submission  read-write
/workspace/work               read-write
/tmp                           private tmpfs
/home/agent                    private tmpfs
```

Do not mount the Docker socket, a home directory, a complete benchmark
checkout, an evaluator directory, or credential files. If an in-container
agent requires network access, the operator may set `VABENCH_NETWORK` to a
dedicated Docker network and use only operator-owned credentials. Internal
credentials must never be included in the image or task bundle.

After a run, export only the files declared by the task's submission contract.
Hidden scoring is performed once by the private evaluator in a separate
environment.

## Security Boundary

This image protects the runtime mount boundary; it cannot make material secret
after that material has already been published. The tracked r49 release is an
open development benchmark because its evaluator assets are present in this
public repository. A blind external evaluation requires new held-out tasks
whose private evaluator assets have never been committed publicly, with only
their sanitized public bundles supplied to this launcher.

For Harbor exports, use the top-level `environment/` directory as the shared
source and materialize it as `<task>/environment/`. Do not maintain a separate
Dockerfile per benchmark task.
