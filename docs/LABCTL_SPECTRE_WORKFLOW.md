# Labctl Spectre Workflow

> **Historical document — not a current operating guide.**
> Use the [current documentation](README.md) for VABench r53 + EVAS 0.8.7.
> Spectre is conditional on an EVAS change or an explicitly named external protocol, not routine development scoring.

This is the distilled remote Spectre path for vaBench validation. The older
`bridge` and `sui-direct` backends remain in the repository for compatibility,
but new v3 Spectre audits should use `labctl`.

## Why Labctl

The THU lab server logs in with `csh`, while robust transfer and orchestration
need bash, tar, timeout, and argv-safe file handling. `labctl` wraps that split:

- local commands call `labctl` with argv, not fragile inline SSH strings;
- upload and download use tar-based directory transfer;
- complex remote logic runs through `/bin/bash`;
- only the final Cadence setup boundary enters `/bin/csh`;
- filenames with spaces or angle brackets are handled by the transfer layer.

## Distilled Configuration

The effective configuration from the previous direct-SUI flow is:

```bash
export VAEVAS_SPECTRE_BACKEND=labctl
export VAEVAS_SPECTRE_MODE=ax
export VAEVAS_LABCTL_HOST=zhangz@101.6.68.147
export VAEVAS_LABCTL_WORK_ROOT=/home/zhangz/WORK/vaevas-direct-spectre
export VAEVAS_LABCTL_CADENCE_CSHRC=/home/cshrc/.cshrc.cadence.IC618SP201
```

The same values may also be supplied with runner flags:

```bash
--spectre-backend labctl
--labctl-host zhangz@101.6.68.147
--labctl-work-root /home/zhangz/WORK/vaevas-direct-spectre
--cadence-cshrc /home/cshrc/.cshrc.cadence.IC618SP201
```

`--sui-host` and `--sui-work-root` remain accepted aliases so existing scripts
do not break.

## Preflight

Run:

```bash
labctl -v \
  --host 101.6.68.147 \
  --user zhangz \
  --remote-root /home/zhangz/WORK/vaevas-direct-spectre \
  --cadence-cshrc /home/cshrc/.cshrc.cadence.IC618SP201 \
  check
```

The expected healthy shape is:

```text
host=thu-wei
user=zhangz
shell=/bin/csh
bash=/usr/bin/bash
tar=/usr/bin/tar
timeout=/usr/bin/timeout
spectre_path_after_cshrc=/home/cadence/spectre/SPECTRE211Hotfix/tools/bin/spectre
cadence_cshrc_exists=yes
```

## v3 Spectre Audit

The v3 audit runner now defaults to `labctl` unless `VAEVAS_SPECTRE_BACKEND`
overrides it.

Smoke one task:

```bash
python3 scripts/run_v3_spectre_audit.py \
  --root benchmark-vabench-release-v3/tasks \
  --task 365-noise-table-voltage-shaper \
  --split hidden \
  --timeout-s 240 \
  --labctl-host "$VAEVAS_LABCTL_HOST" \
  --labctl-work-root "$VAEVAS_LABCTL_WORK_ROOT" \
  --cadence-cshrc "$VAEVAS_LABCTL_CADENCE_CSHRC" \
  --work-root WORK/spectre-labctl-smoke \
  --out WORK/spectre-labctl-smoke/summary.json
```

Full retained 451-row hidden-gold audit should be split into chunks:

```bash
python3 scripts/run_v3_spectre_audit.py \
  --root benchmark-vabench-release-v3/tasks \
  --start 1 --end 170 \
  --split hidden \
  --timeout-s 240 \
  --labctl-host "$VAEVAS_LABCTL_HOST" \
  --labctl-work-root "$VAEVAS_LABCTL_WORK_ROOT" \
  --cadence-cshrc "$VAEVAS_LABCTL_CADENCE_CSHRC" \
  --work-root WORK/spectre-main-451-labctl/001-170 \
  --out WORK/spectre-main-451-labctl/001-170.json
```

Repeat for `171-340` and `341-505`.

## What Was Kept From the Old Flow

The `labctl` backend intentionally reuses the direct-SUI runner's useful
behavior:

- isolated per-case remote run directories;
- staged Spectre testbench names to avoid AHDL cache collisions;
- `ahdl_include` path rewriting for staged solution files;
- `.tbl`, `.txt`, `.csv`, and `.dat` support-file staging;
- `spectre -64 ... -format psfascii -raw ... +preset=ax`;
- bounded Spectre license queue timeout;
- complete remote directory download before PSF parsing;
- `tran_spectre.csv` generation by the existing PSFASCII parser;
- side-output file availability at the case output root;
- best-effort remote cleanup.

## Legacy Backends

Use `--spectre-backend sui-direct` only when comparing against old evidence or
debugging the pre-labctl SSH path. Use `--spectre-backend bridge` only for
legacy virtuoso-bridge-lite tunnel workflows.
