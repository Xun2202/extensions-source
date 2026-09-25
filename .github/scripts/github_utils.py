import os
import re
import subprocess
import time
from pathlib import Path

REPO_NAME = os.getenv("PUBLISH_REPO", "keiyoushi/extensions")
SOURCE_REPO = os.getenv("SOURCE_REPO", "keiyoushi/extensions-source")
RETRY_ATTEMPTS = 4
RETRY_BASE_DELAY = 60

OVERLAY_MODULES_FILE = os.getenv("OVERLAY_MODULES_FILE", ".github/overlay-modules.txt")
_PKG_NAME_REGEX = re.compile(r"""pkgName\s*=\s*["']([^"']+)["']""")


def load_overlay_modules(source_dir: Path | None = None) -> list[tuple[str, str]] | None:
    """
    Returns the (lang, extension) pairs listed in the overlay modules file, or None when
    the file does not exist (meaning: behave like upstream and build everything).
    """
    root = source_dir or Path.cwd()
    path = root / OVERLAY_MODULES_FILE
    if not path.is_file():
        return None

    modules = []
    for raw in path.read_text("utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        lang, _, extension = line.replace(".", "/").partition("/")
        if not lang or not extension:
            raise ValueError(f"{path}: invalid module line {raw!r}, expected <lang>/<extension>")
        modules.append((lang, extension))
    return modules


def overlay_package_suffixes(source_dir: Path | None = None) -> set[str] | None:
    """
    Returns the applicationId suffixes (``<lang>.<extension>`` or the ``pkgName`` override)
    of the overlay modules, or None when no overlay file exists.
    """
    modules = load_overlay_modules(source_dir)
    if modules is None:
        return None

    root = source_dir or Path.cwd()
    suffixes = set()
    for lang, extension in modules:
        build_file = root / "src" / lang / extension / "build.gradle.kts"
        suffix = f"{lang}.{extension}"
        if build_file.is_file():
            match = _PKG_NAME_REGEX.search(build_file.read_text("utf-8"))
            if match:
                suffix = match.group(1)
        suffixes.add(suffix)
    return suffixes


def run_gh(*args: str, success_errors: tuple[str, ...] = ()) -> str:
    attempt = 1
    delay = RETRY_BASE_DELAY
    while True:
        result = subprocess.run(
            ["gh", *args],
            capture_output=True,
            encoding="utf-8",
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()

        error = result.stderr.lower()
        if any(success_error in error for success_error in success_errors):
            return result.stdout.strip()

        if "secondary rate limit" in error and attempt < RETRY_ATTEMPTS:
            retry_delay = delay
            delay *= 2
        elif "api rate limit exceeded" in error and attempt < RETRY_ATTEMPTS:
            rate_limit = subprocess.run(
                ["gh", "api", "rate_limit", "--jq", ".resources.core.reset"],
                capture_output=True,
                encoding="utf-8",
                check=False,
            )
            retry_delay = RETRY_BASE_DELAY
            if rate_limit.returncode == 0:
                retry_delay = max(
                    int(rate_limit.stdout.strip()) - int(time.time()) + 10,
                    RETRY_BASE_DELAY,
                )
        else:
            raise RuntimeError(f"gh {' '.join(args)} failed: {result.stderr.strip()}")

        print(
            f"GitHub rate limit hit; retrying in {retry_delay}s "
            f"(attempt {attempt}/{RETRY_ATTEMPTS})"
        )
        time.sleep(retry_delay)
        attempt += 1
