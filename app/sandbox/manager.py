import re
import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path, PurePosixPath

from ..state import VerificationResult, VerificationStatus


SANDBOX_TIMEOUT_SECONDS = 30
SANDBOX_IMAGE = "codevitals-v6-sandbox:latest"
ALLOWED_VERIFICATION_COMMANDS = {"pytest", "python -m pytest"}
MAX_OUTPUT_CHARS = 5000


class SandboxManager:
    def __init__(self, docker_executable="docker"):
        self.docker_executable = docker_executable

    @staticmethod
    def _validate_patch_paths(patch):
        if not patch or not patch.strip():
            return False, "The proposed patch is empty."

        for line in patch.splitlines():
            if not (line.startswith("--- ") or line.startswith("+++ ")):
                continue
            path = line[4:].split("\t", 1)[0].split(" ", 1)[0]
            if path == "/dev/null":
                continue
            if path.startswith(("a/", "b/")):
                path = path[2:]
            parsed = PurePosixPath(path)
            if parsed.is_absolute() or ".." in parsed.parts:
                return False, "Patch paths must remain inside the sandbox repository."
            if ".codevitals.patch" in parsed.parts:
                return False, "Patch cannot modify the temporary patch file."

        if not any(line.startswith("--- ") for line in patch.splitlines()):
            return False, "Patch is not a unified diff."
        return True, None

    def _docker_base_command(self, workdir, container_name):
        return [
            self.docker_executable,
            "run",
            "--rm",
            "--name",
            container_name,
            "--network=none",
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--pids-limit=128",
            "--memory=512m",
            "--cpus=1",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=64m",
            "--mount",
            f"type=bind,src={workdir},dst=/workspace",
            "--workdir",
            "/workspace",
            "--env",
            "HOME=/tmp",
            "--env",
            "PYTHONDONTWRITEBYTECODE=1",
            SANDBOX_IMAGE,
        ]

    def _ensure_image(self):
        inspect = subprocess.run(
            [self.docker_executable, "image", "inspect", SANDBOX_IMAGE],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        if inspect.returncode == 0:
            return

        dockerfile = Path(__file__).resolve().parents[2] / "sandbox" / "Dockerfile"
        build = subprocess.run(
            [
                self.docker_executable,
                "build",
                "--tag",
                SANDBOX_IMAGE,
                "--file",
                str(dockerfile),
                str(dockerfile.parent),
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
        if build.returncode != 0:
            raise RuntimeError(
                (build.stderr or build.stdout or "Unable to build sandbox image.")[-MAX_OUTPUT_CHARS:]
            )

    def verify(self, repository_path, finding_id, proposed_patch, verification_command):
        started = time.monotonic()
        result = VerificationResult(
            finding_id=finding_id,
            status=VerificationStatus.ERROR.value,
        )

        if proposed_patch is None or not str(proposed_patch).strip():
            result.status = VerificationStatus.NOT_REQUESTED.value
            return result

        if verification_command not in ALLOWED_VERIFICATION_COMMANDS:
            result.error = "Verification command is not allowed."
            return result

        valid_patch, patch_error = self._validate_patch_paths(proposed_patch)
        if not valid_patch:
            result.status = VerificationStatus.FAILED.value
            result.error = patch_error
            return result

        sandbox_root = None
        output_parts = []
        container_names = []
        try:
            repository = Path(repository_path).resolve(strict=True)
            if not repository.is_dir():
                raise ValueError("Repository path is not a directory.")

            sandbox_root = Path(tempfile.mkdtemp(prefix="codevitals-sandbox-"))
            workdir = sandbox_root / "repository"
            shutil.copytree(
                repository,
                workdir,
                symlinks=True,
                ignore=shutil.ignore_patterns(
                    ".git", "venv", ".venv", "__pycache__"
                ),
            )
            (workdir / ".codevitals.patch").write_text(
                proposed_patch,
                encoding="utf-8",
            )

            self._ensure_image()
            deadline = time.monotonic() + SANDBOX_TIMEOUT_SECONDS
            patch_container = "codevitals-patch-" + uuid.uuid4().hex[:12]
            container_names.append(patch_container)
            patch_process = subprocess.run(
                self._docker_base_command(workdir, patch_container)
                + ["patch", "--batch", "--forward", "-p1", "-i", "/workspace/.codevitals.patch"],
                capture_output=True,
                text=True,
                check=False,
                timeout=max(0.01, deadline - time.monotonic()),
            )
            output_parts.extend(part for part in (patch_process.stdout, patch_process.stderr) if part)
            result.output = "\n".join(output_parts)[-MAX_OUTPUT_CHARS:]
            if patch_process.returncode != 0:
                result.status = VerificationStatus.FAILED.value
                result.error = "Proposed patch could not be applied inside the sandbox."
                return result

            test_args = (
                ["pytest"]
                if verification_command == "pytest"
                else ["python", "-m", "pytest"]
            )
            test_container = "codevitals-test-" + uuid.uuid4().hex[:12]
            container_names.append(test_container)
            test_process = subprocess.run(
                self._docker_base_command(workdir, test_container) + test_args,
                capture_output=True,
                text=True,
                check=False,
                timeout=max(0.01, deadline - time.monotonic()),
            )
            output_parts.extend(part for part in (test_process.stdout, test_process.stderr) if part)
            result.output = "\n".join(output_parts)[-MAX_OUTPUT_CHARS:]
            result.tests_run = sum(
                int(value)
                for value in re.findall(r"(\d+)\s+(?:passed|failed|error|errors)", result.output)
            )
            passed = re.search(r"(\d+)\s+passed", result.output)
            failed = re.search(r"(\d+)\s+failed", result.output)
            errors = re.search(r"(\d+)\s+errors?", result.output)
            result.tests_passed = int(passed.group(1)) if passed else 0
            result.tests_failed = (int(failed.group(1)) if failed else 0) + (
                int(errors.group(1)) if errors else 0
            )
            result.status = (
                VerificationStatus.VERIFIED.value
                if test_process.returncode == 0
                else VerificationStatus.FAILED.value
            )
            return result
        except subprocess.TimeoutExpired as exc:
            captured = [exc.stdout, exc.stderr]
            output_parts.extend(
                item.decode("utf-8", errors="replace") if isinstance(item, bytes) else item
                for item in captured
                if item
            )
            result.status = VerificationStatus.TIMEOUT.value
            result.output = "\n".join(output_parts)[-MAX_OUTPUT_CHARS:]
            result.error = "Sandbox verification exceeded the 30-second timeout."
            return result
        except Exception as exc:
            result.status = VerificationStatus.ERROR.value
            result.error = str(exc)[:MAX_OUTPUT_CHARS]
            return result
        finally:
            result.duration_seconds = time.monotonic() - started
            for container_name in container_names:
                try:
                    subprocess.run(
                        [self.docker_executable, "rm", "--force", container_name],
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=5,
                    )
                except Exception:
                    pass
            if sandbox_root is not None:
                shutil.rmtree(sandbox_root, ignore_errors=True)
