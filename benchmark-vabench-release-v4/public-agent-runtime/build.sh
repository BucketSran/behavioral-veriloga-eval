#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)

IMAGE_TAG="${IMAGE_TAG:-vabench-agent-runtime:0.8.4}"
NOEXEC_IMAGE_TAG="${NOEXEC_IMAGE_TAG:-vabench-agent-runtime:0.8.4-noexec}"
PLATFORM="${PLATFORM:-linux/amd64}"
DOCKER="${DOCKER:-docker}"

"$DOCKER" buildx build \
    --platform "$PLATFORM" \
    --pull \
    --load \
    --tag "$IMAGE_TAG" \
    "$REPO_ROOT/environment"

"$DOCKER" buildx build \
    --platform "$PLATFORM" \
    --build-arg VABENCH_EXECUTABLE_FEEDBACK=0 \
    --load \
    --tag "$NOEXEC_IMAGE_TAG" \
    "$REPO_ROOT/environment"

"$DOCKER" image inspect "$IMAGE_TAG" --format '{{.Id}}'
"$DOCKER" image inspect "$NOEXEC_IMAGE_TAG" --format '{{.Id}}'
