import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from app.analyzer import make_finding_id
from app.harness import AgentHarness
from app.rag.retriever import retrieve
from app.sandbox.manager import SandboxManager
from app.state import VerificationStatus


PATCH = """--- a/app.py
+++ b/app.py
@@ -1 +1 @@
-value = 1
+value = 2
"""


def completed(returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess([], returncode, stdout, stderr)


class SandboxUnitTests(unittest.TestCase):
    def setUp(self):
        self.temp_root = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp_root.name) / "repo"
        self.repo.mkdir()
        (self.repo / "app.py").write_text("value = 1\n", encoding="utf-8")
        (self.repo / "test_app.py").write_text(
            "from app import value\n\ndef test_value():\n    assert value == 2\n",
            encoding="utf-8",
        )
        self.manager = SandboxManager()
        self.manager._ensure_image = Mock()

    def tearDown(self):
        self.temp_root.cleanup()

    def docker_runner(self, patch_code=0, pytest_code=0):
        commands = []

        def run(command, **kwargs):
            commands.append(command)
            if command[1:3] == ["rm", "--force"]:
                return completed()
            if "patch" in command:
                return completed(patch_code, "patch output\n")
            if "pytest" in command:
                summary = "2 passed\n" if pytest_code == 0 else "1 failed\n"
                return completed(pytest_code, summary)
            self.fail("Unexpected docker command")

        return commands, run

    def test_success_runs_allowlisted_tests_in_sandbox_only(self):
        original = (self.repo / "app.py").read_bytes()
        commands, runner = self.docker_runner()
        created_paths = []
        real_mkdtemp = tempfile.mkdtemp

        def make_temp(*args, **kwargs):
            path = real_mkdtemp(*args, **kwargs)
            created_paths.append(path)
            return path

        with patch("app.sandbox.manager.subprocess.run", side_effect=runner):
            with patch("app.sandbox.manager.tempfile.mkdtemp", side_effect=make_temp):
                result = self.manager.verify(str(self.repo), "FND-test", PATCH, "pytest")
        self.assertEqual(result.status, VerificationStatus.VERIFIED.value)
        self.assertEqual(result.tests_passed, 2)
        self.assertEqual((self.repo / "app.py").read_bytes(), original)
        sandbox_path = Path(created_paths[0])
        self.assertFalse(sandbox_path.exists())
        runtime_commands = [command for command in commands if command[1] == "run"]
        self.assertEqual(len(runtime_commands), 2)
        for command in runtime_commands:
            self.assertIn("--network=none", command)
            self.assertIn("--read-only", command)
            self.assertIn("--cap-drop=ALL", command)
            self.assertNotIn("--privileged", command)
            self.assertFalse(any("docker.sock" in arg for arg in command))
            self.assertTrue(any(arg.startswith("type=bind,src=") for arg in command))

    def test_patch_failure_is_failed_and_original_unchanged(self):
        original = (self.repo / "app.py").read_bytes()
        commands, runner = self.docker_runner(patch_code=1)
        with patch("app.sandbox.manager.subprocess.run", side_effect=runner):
            result = self.manager.verify(str(self.repo), "FND-test", PATCH, "pytest")
        self.assertEqual(result.status, VerificationStatus.FAILED.value)
        self.assertEqual((self.repo / "app.py").read_bytes(), original)
        self.assertFalse(any("pytest" in command for command in commands))

    def test_failing_pytest_is_failed(self):
        commands, runner = self.docker_runner(pytest_code=1)
        with patch("app.sandbox.manager.subprocess.run", side_effect=runner):
            result = self.manager.verify(str(self.repo), "FND-test", PATCH, "python -m pytest")
        self.assertEqual(result.status, VerificationStatus.FAILED.value)
        self.assertEqual(result.tests_failed, 1)
        test_command = next(
            command
            for command in commands
            if command[1] == "run" and command[-2:] == ["-m", "pytest"]
        )
        self.assertIn("python", test_command)

    def test_timeout_returns_timeout_and_forces_container_removal(self):
        commands = []

        def run(command, **kwargs):
            commands.append(command)
            if command[1:3] == ["rm", "--force"]:
                return completed()
            raise subprocess.TimeoutExpired(command, kwargs.get("timeout"))

        with patch("app.sandbox.manager.subprocess.run", side_effect=run):
            result = self.manager.verify(str(self.repo), "FND-test", PATCH, "pytest")
        self.assertEqual(result.status, VerificationStatus.TIMEOUT.value)
        self.assertTrue(any(command[1:3] == ["rm", "--force"] for command in commands))

    def test_invalid_command_and_patch_are_rejected_before_docker(self):
        with patch("app.sandbox.manager.subprocess.run") as docker_run:
            result = self.manager.verify(str(self.repo), "FND-test", PATCH, "pytest; rm -rf /")
            broken = self.manager.verify(str(self.repo), "FND-test", "not a diff", "pytest")
        self.assertEqual(result.status, VerificationStatus.ERROR.value)
        self.assertEqual(broken.status, VerificationStatus.FAILED.value)
        docker_run.assert_not_called()


class HarnessTests(unittest.TestCase):
    def test_disallowed_command_is_rejected_without_sandbox_execution(self):
        candidate = {
            "category": "security",
            "file": "app.py",
            "line": 1,
            "title": "Potential issue",
        }
        finding_id = make_finding_id(**candidate)
        harness = AgentHarness("/tmp", [candidate])
        harness.tool_manager.sandbox_manager.verify = Mock()
        result = harness.execute_tool(
            "verify_fix",
            {
                "finding_id": finding_id,
                "proposed_patch": PATCH,
                "verification_command": "bash -c id",
            },
        )
        self.assertEqual(result["status"], "blocked")
        harness.tool_manager.sandbox_manager.verify.assert_not_called()
        self.assertEqual(harness.budget.tool_calls_used, 0)


class RAGRegressionTests(unittest.TestCase):
    def test_security_guidance_retrieval_remains_available(self):
        results = retrieve("SQL injection")
        self.assertTrue(results)


@unittest.skipUnless(shutil.which("docker"), "Docker CLI is unavailable")
class DockerIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            info = subprocess.run(
                ["docker", "info"], capture_output=True, text=True, timeout=5
            )
        except Exception as exc:
            raise unittest.SkipTest("Docker daemon is unavailable: " + str(exc))
        if info.returncode != 0:
            raise unittest.SkipTest("Docker daemon is unavailable")

    def setUp(self):
        self.temp_root = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp_root.name) / "repo"
        self.repo.mkdir()
        (self.repo / "app.py").write_text("value = 1\n", encoding="utf-8")
        (self.repo / "test_app.py").write_text(
            "from app import value\n\ndef test_value():\n    assert value == 2\n",
            encoding="utf-8",
        )
        self.manager = SandboxManager()

    def tearDown(self):
        self.temp_root.cleanup()

    def test_successful_patch_preserves_original_and_destroys_copy(self):
        original = (self.repo / "app.py").read_bytes()
        created_paths = []
        real_mkdtemp = tempfile.mkdtemp

        def make_temp(*args, **kwargs):
            path = real_mkdtemp(*args, **kwargs)
            created_paths.append(path)
            return path

        with patch("app.sandbox.manager.tempfile.mkdtemp", side_effect=make_temp):
            result = self.manager.verify(str(self.repo), "FND-pass", PATCH, "pytest")
        self.assertEqual(result.status, VerificationStatus.VERIFIED.value)
        self.assertEqual((self.repo / "app.py").read_bytes(), original)
        self.assertFalse(Path(created_paths[0]).exists())

    def test_patch_failure_and_failing_test_preserve_original(self):
        original = (self.repo / "app.py").read_bytes()
        bad_patch = PATCH.replace("value = 1", "missing = 1")
        patch_result = self.manager.verify(str(self.repo), "FND-bad", bad_patch, "pytest")
        self.assertEqual(patch_result.status, VerificationStatus.FAILED.value)

        (self.repo / "test_app.py").write_text(
            "from app import value\n\ndef test_value():\n    assert value == 3\n",
            encoding="utf-8",
        )
        test_result = self.manager.verify(str(self.repo), "FND-fail", PATCH, "python -m pytest")
        self.assertEqual(test_result.status, VerificationStatus.FAILED.value)
        self.assertEqual((self.repo / "app.py").read_bytes(), original)
