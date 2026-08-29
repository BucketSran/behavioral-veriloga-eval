FROM python:3.11.13-slim-bookworm@sha256:86adf8dbadc3d6e82ee5dd2c74bec2e1c2467cdad47886280501df722372d2e1

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/home/agent \
    PATH=/usr/local/bin:/usr/bin:/bin

ARG VABENCH_EXECUTABLE_FEEDBACK=1

COPY evaluator-contract.json /opt/vabench-evaluator-contract.json
COPY requirements.lock /tmp/requirements.lock
RUN python3 -m pip install --no-cache-dir --require-hashes -r /tmp/requirements.lock \
    && rm /tmp/requirements.lock \
    && evas --version --format json > /tmp/evas-identity.json \
    && python3 -c 'import json; p=json.load(open("/tmp/evas-identity.json")); c=json.load(open("/opt/vabench-evaluator-contract.json"))["evaluator"]["evas"]; assert p["package_version"] == "0.8.7" and p["engine"] == "evas-rust" and p["rust_core_present"] and p["rust_core_loadable"] and p["rust_core_abi_version"] == 20260718 and p["rust_core_version"] == "0.2.4"; assert all(p[k] == c[k] for k in ("package_name", "package_version", "engine", "rust_core_present", "rust_core_loadable", "rust_core_abi_version", "rust_core_version"))' \
    && rm /tmp/evas-identity.json \
    && if [ "$VABENCH_EXECUTABLE_FEEDBACK" = "0" ]; then \
         python3 -m pip uninstall -y evas-sim && hash -r; \
       fi \
    && if [ "$VABENCH_EXECUTABLE_FEEDBACK" = "1" ]; then \
         command -v evas >/dev/null; \
       else \
         ! command -v evas >/dev/null \
         && python3 -c 'import importlib.util; assert importlib.util.find_spec("evas") is None'; \
       fi

COPY runtime/entrypoint.sh /usr/local/bin/vabench-entrypoint
RUN chmod 0555 /usr/local/bin/vabench-entrypoint \
    && mkdir -p /workspace/public/task /workspace/public/submission /workspace/work /home/agent \
    && chown -R 10001:10001 /workspace /home/agent

USER 10001:10001
WORKDIR /workspace
ENTRYPOINT ["/usr/local/bin/vabench-entrypoint"]
CMD ["/bin/bash"]
