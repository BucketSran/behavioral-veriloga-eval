import os
from pathlib import Path
import subprocess
import tempfile
import unittest


RUNTIME_DIR = Path(__file__).resolve().parents[2] / "public-agent-runtime"
REPO_ROOT = Path(__file__).resolve().parents[3]
ENVIRONMENT_DIR = REPO_ROOT / "environment"


class PublicAgentRuntimeTest(unittest.TestCase):
    def test_verifier_uses_operator_shared_temp_root(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            shared_root = Path(temp_dir)
            docker_log = shared_root / "docker-args.txt"
            fake_docker = shared_root / "docker"
            fake_docker.write_text(
                "#!/bin/sh\n"
                "printf '%s\\n' \"$@\" > \"$VABENCH_DOCKER_LOG\"\n",
                encoding="utf-8",
            )
            fake_docker.chmod(0o755)
            env = os.environ.copy()
            env.update(
                {
                    "DOCKER": str(fake_docker),
                    "VABENCH_DOCKER_LOG": str(docker_log),
                    "VABENCH_DOCKER_SHARED_TMPDIR": str(shared_root),
                }
            )

            subprocess.run(
                [str(RUNTIME_DIR / "verify.sh")],
                check=True,
                cwd=RUNTIME_DIR,
                env=env,
                capture_output=True,
                text=True,
            )

            docker_args = docker_log.read_text(encoding="utf-8")
            self.assertIn(f"src={shared_root}/", docker_args)
            self.assertNotIn("/var/folders/", docker_args)

    def test_docker_build_context_is_allowlisted(self) -> None:
        dockerignore = (ENVIRONMENT_DIR / ".dockerignore").read_text(encoding="utf-8")
        self.assertEqual(dockerignore.splitlines()[0], "*")
        self.assertIn("!Dockerfile", dockerignore)
        self.assertIn("!requirements.lock", dockerignore)
        self.assertIn("!runtime/entrypoint.sh", dockerignore)

    def test_runtime_image_is_pinned_and_non_root(self) -> None:
        dockerfile = (ENVIRONMENT_DIR / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("FROM python:3.10.14-slim-bookworm@sha256:", dockerfile)
        self.assertIn("pip install --no-cache-dir --require-hashes", dockerfile)
        self.assertIn('"package_version"] == "0.8.4"', dockerfile)
        self.assertIn("USER 10001:10001", dockerfile)
        self.assertNotIn("COPY .", dockerfile)

    def test_runtime_build_produces_matched_agentic_and_noexec_images(self) -> None:
        dockerfile = (ENVIRONMENT_DIR / "Dockerfile").read_text(encoding="utf-8")
        build = (RUNTIME_DIR / "build.sh").read_text(encoding="utf-8")
        verify = (RUNTIME_DIR / "verify.sh").read_text(encoding="utf-8")

        self.assertIn("ARG VABENCH_EXECUTABLE_FEEDBACK=1", dockerfile)
        self.assertIn("pip uninstall -y evas-sim", dockerfile)
        self.assertIn("command -v evas", dockerfile)
        self.assertIn("VABENCH_EXECUTABLE_FEEDBACK=0", build)
        self.assertIn("vabench-agent-runtime:0.8.4-noexec", build)
        self.assertIn("vabench-agent-runtime:0.8.4-noexec", verify)
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
        self.assertIn("evas-sim==0.8.4", lock)
        packages = [
            line
            for line in lock.splitlines()
            if line and not line[0].isspace() and "==" in line
        ]
        self.assertTrue(packages)
        for package in packages:
            self.assertTrue(package.endswith(" \\"))

    def test_active_experiment_entrypoints_use_evas_084(self) -> None:
        expected_fragments = {
            REPO_ROOT / "pyproject.toml": '"evas-sim==0.8.4"',
            ENVIRONMENT_DIR / "requirements.in": "evas-sim==0.8.4",
            RUNTIME_DIR / "build.sh": "vabench-agent-runtime:0.8.4",
            RUNTIME_DIR / "run.sh": "vabench-agent-runtime:0.8.4",
            RUNTIME_DIR / "verify.sh": "vabench-agent-runtime:0.8.4",
            REPO_ROOT
            / "benchmark-vabench-release-v4"
            / "runners"
            / "run_benchmarkv4_campaign.py": "vabench-agent-runtime:0.8.4",
            REPO_ROOT
            / "benchmark-vabench-release-v4"
            / "operations"
            / "calibration_pilot"
            / "mini_swe_vabench.py": "vabench-agent-runtime:0.8.4",
            REPO_ROOT
            / "benchmark-vabench-release-v4"
            / "runners"
            / "derived_testbench_oracle.py": 'REQUIRED_EVAS_VERSION = "0.8.4"',
            REPO_ROOT
            / "benchmark-vabench-release-v4"
            / "runners"
            / "feedback_oracle.py": 'REQUIRED_EVAS_VERSION = "0.8.4"',
        }
        for path, expected in expected_fragments.items():
            with self.subTest(path=path):
                self.assertIn(expected, path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
