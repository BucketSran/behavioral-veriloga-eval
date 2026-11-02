#!/bin/sh
set -eu

usage() {
    echo "usage: $0 TASK_DIR SUBMISSION_DIR WORK_DIR [AGENT_COMMAND ...]" >&2
    exit 64
}

[ "$#" -ge 3 ] || usage

TASK_INPUT=$1
SUBMISSION_INPUT=$2
WORK_INPUT=$3
shift 3

[ -d "$TASK_INPUT" ] || { echo "task directory does not exist: $TASK_INPUT" >&2; exit 66; }
mkdir -p "$SUBMISSION_INPUT" "$WORK_INPUT"

TASK_DIR=$(cd "$TASK_INPUT" && pwd -P)
SUBMISSION_DIR=$(cd "$SUBMISSION_INPUT" && pwd -P)
WORK_DIR=$(cd "$WORK_INPUT" && pwd -P)
SKILLS_ARG=
if [ "${VABENCH_SKILLS_DIR:-}" ]; then
    [ -d "$VABENCH_SKILLS_DIR" ] || { echo "skills directory does not exist: $VABENCH_SKILLS_DIR" >&2; exit 66; }
    SKILLS_DIR=$(cd "$VABENCH_SKILLS_DIR" && pwd -P)
    SKILLS_ARG="--mount=type=bind,src=$SKILLS_DIR,dst=/workspace/public/skills,readonly"
fi

IMAGE_TAG="${IMAGE_TAG:-vabench-agent-runtime:0.8.4}"
DOCKER="${DOCKER:-docker}"
NETWORK="${VABENCH_NETWORK:-none}"
HOST_UID="${VABENCH_UID:-${SUDO_UID:-$(id -u)}}"
HOST_GID="${VABENCH_GID:-${SUDO_GID:-$(id -g)}}"

if [ "$#" -eq 0 ]; then
    set -- /bin/bash
fi

TTY_ARGS=-i
if [ -t 0 ] && [ -t 1 ]; then
    TTY_ARGS=-it
fi

# TTY_ARGS is intentionally word-split as a single Docker option.
# shellcheck disable=SC2086
exec "$DOCKER" run --rm $TTY_ARGS \
    --platform linux/amd64 \
    --read-only \
    --cap-drop=ALL \
    --security-opt=no-new-privileges \
    --user "$HOST_UID:$HOST_GID" \
    --pids-limit=512 \
    --memory=4g \
    --cpus=2 \
    --network="$NETWORK" \
    --tmpfs /tmp:rw,nosuid,nodev,size=2g,mode=1777 \
    --tmpfs "/home/agent:rw,nosuid,nodev,size=256m,mode=0700,uid=$HOST_UID,gid=$HOST_GID" \
    --mount "type=bind,src=$TASK_DIR,dst=/workspace/public/task,readonly" \
    ${SKILLS_ARG:+"$SKILLS_ARG"} \
    --mount "type=bind,src=$SUBMISSION_DIR,dst=/workspace/public/submission" \
    --mount "type=bind,src=$WORK_DIR,dst=/workspace/work" \
    --workdir /workspace \
    "$IMAGE_TAG" "$@"
