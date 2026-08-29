import json
from pathlib import Path
import unittest


RUNTIME_DIR = Path(__file__).resolve().parents[2] / "public-agent-runtime"
REPO_ROOT = Path(__file__).resolve().parents[3]
ENVIRONMENT_DIR = REPO_ROOT / "environment"
CONTRACT = ENVIRONMENT_DIR / "evaluator-contract.json"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "public-agent-runtime.yml"
CAMPAIGN_RUNNER = (
    REPO_ROOT
    / "benchmark-vabench-release-v4"
    / "runners"
    / "run_benchmarkv4_campaign.py"
)
MINI_SWE_ADAPTER = (
    REPO_ROOT
    / "benchmark-vabench-release-v4"
    / "operations"
    / "calibration_pilot"
    / "mini_swe_vabench.py"
)


class PublicAgentRuntimeTest(unittest.TestCase):
    def test_docker_build_context_is_allowlisted(self) -> None:
        dockerignore = (ENVIRONMENT_DIR / ".dockerignore").read_text(encoding="utf-8")
        self.assertEqual(dockerignore.splitlines()[0], "*")
        self.assertIn("!Dockerfile", dockerignore)
        self.assertIn("!evaluator-contract.json", dockerignore)
        self.assertIn("!requirements.lock", dockerignore)
        self.assertIn("!runtime/entrypoint.sh", dockerignore)

    def test_runtime_image_is_pinned_and_non_root(self) -> None:
        dockerfile = (ENVIRONMENT_DIR / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("FROM python:3.11.13-slim-bookworm@sha256:", dockerfile)
        self.assertIn("COPY evaluator-contract.json /opt/vabench-evaluator-contract.json", dockerfile)
        self.assertIn("pip install --no-cache-dir --require-hashes", dockerfile)
        self.assertIn('"package_version"] == "0.8.7"', dockerfile)
        self.assertIn('"engine"] == "evas-rust"', dockerfile)
        self.assertIn('"rust_core_abi_version"] == 20260718', dockerfile)
        self.assertIn('"rust_core_version"] == "0.2.4"', dockerfile)
        self.assertIn("USER 10001:10001", dockerfile)
        self.assertNotIn("COPY .", dockerfile)

    def test_machine_readable_evaluator_contract_matches_runtime(self) -> None:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(contract["schema_version"], "vabench-evaluator-environment-contract-v1")
        self.assertEqual(contract["python"]["version"], "3.11.13")
        self.assertEqual(contract["dependencies"]["packages"]["evas-sim"], "0.8.7")
        self.assertEqual(contract["evaluator"]["formal_judge"], "pinned_strict_evas")
        self.assertFalse(contract["evaluator"]["spectre_required"])
        self.assertEqual(contract["evaluator"]["evas"]["engine"], "evas-rust")
        self.assertEqual(contract["evaluator"]["evas"]["rust_core_abi_version"], 20260718)
        self.assertEqual(contract["evaluator"]["evas"]["rust_core_version"], "0.2.4")
        mount_targets = {
            item["target"]: item["mode"]
            for item in contract["runtime_boundary"]["model_mounts"]
        }
        self.assertEqual(
            mount_targets,
            {
                "/workspace/public/task": "ro",
                "/workspace/public/submission": "rw",
                "/workspace/work": "rw",
                "/workspace/public/skills": "ro",
            },
        )
        self.assertIn("/workspace/evaluator", contract["runtime_boundary"]["forbidden_model_paths"])
        self.assertIn("/opt/benchmark", contract["runtime_boundary"]["forbidden_model_paths"])

    def test_runtime_build_produces_matched_evas_and_no_evas_images(self) -> None:
        dockerfile = (ENVIRONMENT_DIR / "Dockerfile").read_text(encoding="utf-8")
        build = (RUNTIME_DIR / "build.sh").read_text(encoding="utf-8")
        verify = (RUNTIME_DIR / "verify.sh").read_text(encoding="utf-8")

        self.assertIn("ARG VABENCH_EXECUTABLE_FEEDBACK=1", dockerfile)
        self.assertIn("python3 -m pip uninstall -y evas-sim", dockerfile)
        self.assertIn("vabench-agent-runtime:0.8.7-no-evas", build)
        self.assertIn("--build-arg VABENCH_EXECUTABLE_FEEDBACK=0", build)
        self.assertEqual(build.count("--pull"), 2)
        self.assertIn("vabench-agent-runtime:0.8.7-no-evas", verify)
        self.assertIn("! command -v evas >/dev/null", verify)
        self.assertIn('find_spec("evas") is None', verify)

    def test_launcher_exposes_only_public_runtime_mounts(self) -> None:
        launcher = (RUNTIME_DIR / "run.sh").read_text(encoding="utf-8")
        self.assertIn("--read-only", launcher)
        self.assertIn("--cap-drop=ALL", launcher)
        self.assertIn("--security-opt=no-new-privileges", launcher)
        self.assertIn('--user "$HOST_UID:$HOST_GID"', launcher)
        self.assertIn("--network=\"$NETWORK\"", launcher)
        self.assertEqual(launcher.count("--mount"), 4)
        self.assertIn("dst=/workspace/public/task,readonly", launcher)
        self.assertIn("dst=/workspace/public/skills,readonly", launcher)
        self.assertIn('if [ "${VABENCH_SKILLS_DIR:-}" ]', launcher)
        self.assertIn("dst=/workspace/public/submission", launcher)
        self.assertIn("dst=/workspace/work", launcher)
        self.assertNotIn("benchmark", launcher.lower())
        self.assertNotIn("evaluator", launcher.lower())

    def test_evas_and_all_dependencies_are_hash_locked(self) -> None:
        lock = (ENVIRONMENT_DIR / "requirements.lock").read_text(encoding="utf-8")
        self.assertIn("pip-compile with Python 3.11", lock)
        self.assertIn("evas-sim==0.8.7", lock)
        packages = [
            line
            for line in lock.splitlines()
            if line and not line[0].isspace() and "==" in line
        ]
        self.assertTrue(packages)
        for package in packages:
            self.assertTrue(package.endswith(" \\"))

    def test_runtime_entrypoints_share_the_evas_084_image_lock(self) -> None:
        expected = "vabench-agent-runtime:0.8.7"
        surfaces = [
            RUNTIME_DIR / "build.sh",
            RUNTIME_DIR / "run.sh",
            RUNTIME_DIR / "verify.sh",
            WORKFLOW,
            CAMPAIGN_RUNNER,
            MINI_SWE_ADAPTER,
        ]
        for surface in surfaces:
            text = surface.read_text(encoding="utf-8")
            self.assertIn(expected, text, surface)
            self.assertNotIn("vabench-agent-runtime:0.8.3", text, surface)

    def test_verifier_uses_a_docker_shared_temporary_directory(self) -> None:
        verifier = (RUNTIME_DIR / "verify.sh").read_text(encoding="utf-8")
        self.assertIn('mktemp -d "$PWD/.verify.XXXXXX"', verifier)
        self.assertNotIn("TMP_ROOT=$(mktemp -d)", verifier)


if __name__ == "__main__":
    unittest.main()
