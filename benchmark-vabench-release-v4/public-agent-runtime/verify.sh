#!/bin/sh
set -eu

cd "$(dirname "$0")"

IMAGE_TAG="${IMAGE_TAG:-vabench-agent-runtime:0.8.4}"
NOEXEC_IMAGE_TAG="${NOEXEC_IMAGE_TAG:-vabench-agent-runtime:0.8.4-noexec}"
DOCKER="${DOCKER:-docker}"
SHARED_TMP_PARENT="${VABENCH_DOCKER_SHARED_TMPDIR:-$PWD}"
mkdir -p "$SHARED_TMP_PARENT"
SHARED_TMP_PARENT=$(cd "$SHARED_TMP_PARENT" && pwd -P)
TMP_ROOT=$(mktemp -d "$SHARED_TMP_PARENT/.vabench-runtime-verify.XXXXXX")
trap 'rm -rf "$TMP_ROOT"' EXIT INT TERM

mkdir -p "$TMP_ROOT/task" "$TMP_ROOT/submission" "$TMP_ROOT/work"
chmod 0777 "$TMP_ROOT/submission" "$TMP_ROOT/work"

cat > "$TMP_ROOT/task/smoke.va" <<'EOF'
`include "disciplines.vams"
module smoke(in, out);
input in; output out; electrical in, out;
analog V(out) <+ V(in);
endmodule
EOF

cat > "$TMP_ROOT/task/visible_test.scs" <<'EOF'
simulator lang=spectre
global 0
ahdl_include "smoke.va"
VIN (in 0) vsource type=pwl wave=[0 0 1n 0 2n 0.9 3n 0.9]
XDUT (in out) smoke
tran tran stop=3n maxstep=100p
save in out
EOF

"$DOCKER" run --rm \
    --platform linux/amd64 \
    --read-only \
    --cap-drop=ALL \
    --security-opt=no-new-privileges \
    --network=none \
    --tmpfs /tmp:rw,nosuid,nodev,size=256m,mode=1777 \
    --tmpfs /home/agent:rw,nosuid,nodev,size=64m,mode=0700,uid=10001,gid=10001 \
    --mount "type=bind,src=$TMP_ROOT/task,dst=/workspace/public/task,readonly" \
    --mount "type=bind,src=$TMP_ROOT/submission,dst=/workspace/public/submission" \
    --mount "type=bind,src=$TMP_ROOT/work,dst=/workspace/work" \
    "$IMAGE_TAG" /bin/bash -lc '
        set -eu
        test -r public/task/visible_test.scs
        test ! -w public/task/visible_test.scs
        test -w public/submission
        test -w work
        evas --version --format json > work/evas-identity.json
        evas simulate public/task/visible_test.scs -o /tmp/vabench-visible/evas-output --spectre-strict
        test -s /tmp/vabench-visible/evas-output/tran.csv
        python3 - <<"PY"
import csv
import json

identity = json.load(open("work/evas-identity.json", encoding="utf-8"))
assert identity["package_version"] == "0.8.4"
assert identity["rust_core_present"] is True
assert identity["rust_core_loadable"] is True
with open("/tmp/vabench-visible/evas-output/tran.csv", newline="", encoding="utf-8") as handle:
    rows = list(csv.DictReader(handle))
assert rows and {"time", "in", "out"}.issubset(rows[0])
print(f"PASS: EVAS waveform is readable ({len(rows)} rows)")
PY
        test ! -e /opt/benchmark
        test ! -e /workspace/evaluator
    '

"$DOCKER" run --rm \
    --platform linux/amd64 \
    --read-only \
    --cap-drop=ALL \
    --security-opt=no-new-privileges \
    --network=none \
    --tmpfs /tmp:rw,nosuid,nodev,size=256m,mode=1777 \
    --tmpfs /home/agent:rw,nosuid,nodev,size=64m,mode=0700,uid=10001,gid=10001 \
    --mount "type=bind,src=$TMP_ROOT/task,dst=/workspace/public/task,readonly" \
    --mount "type=bind,src=$TMP_ROOT/submission,dst=/workspace/public/submission" \
    --mount "type=bind,src=$TMP_ROOT/work,dst=/workspace/work" \
    "$NOEXEC_IMAGE_TAG" /bin/bash -lc '
        set -eu
        test -r public/task/visible_test.scs
        test ! -w public/task/visible_test.scs
        test -w public/submission
        test -w work
        ! command -v evas >/dev/null
        python3 - <<"PY"
import importlib.util
assert importlib.util.find_spec("evas") is None
PY
        test ! -e /opt/benchmark
        test ! -e /workspace/evaluator
    '

echo "PASS: matched Agentic and Agent-NoExec images verified"
