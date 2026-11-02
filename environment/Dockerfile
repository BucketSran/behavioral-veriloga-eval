FROM python:3.10.14-slim-bookworm@sha256:2407c61b1a18067393fecd8a22cf6fceede893b6aaca817bf9fbfe65e33614a3

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/home/agent \
    PATH=/usr/local/bin:/usr/bin:/bin

ARG VABENCH_EXECUTABLE_FEEDBACK=1

COPY requirements.lock /tmp/requirements.lock
RUN python3 -m pip install --no-cache-dir --require-hashes -r /tmp/requirements.lock \
    && rm /tmp/requirements.lock \
    && evas --version --format json > /tmp/evas-identity.json \
    && python3 -c 'import json; p=json.load(open("/tmp/evas-identity.json")); assert p["package_version"] == "0.8.4" and p["rust_core_present"] and p["rust_core_loadable"]' \
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
