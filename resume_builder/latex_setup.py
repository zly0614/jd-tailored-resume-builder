from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin
from urllib import request


MIKTEX_DOWNLOAD_PAGE = "https://miktex.org/download"


@dataclass
class LatexInstallResult:
    success: bool
    message: str
    command: str
    engine_path: str


def detect_latex_engine() -> str:
    for candidate in ("xelatex", "pdflatex"):
        found = shutil.which(candidate)
        if found:
            return found
    return ""


def install_latex(provider: str = "auto") -> LatexInstallResult:
    existing = detect_latex_engine()
    if existing:
        return LatexInstallResult(
            success=True,
            message="A LaTeX engine is already installed.",
            command="",
            engine_path=existing,
        )

    system = platform.system().lower()
    if system == "windows":
        return _install_on_windows(provider)

    return LatexInstallResult(
        success=False,
        message="Automatic LaTeX installation is currently implemented for Windows only.",
        command="",
        engine_path="",
    )


def _install_on_windows(provider: str) -> LatexInstallResult:
    if provider in {"auto", "miktex-private"}:
        private_result = _install_miktex_private()
        if private_result.success:
            return private_result
        if provider == "miktex-private":
            return private_result

    if provider in {"auto", "choco"}:
        return _install_with_chocolatey()

    return LatexInstallResult(
        success=False,
        message=f"Unsupported provider: {provider}",
        command="",
        engine_path="",
    )


def _install_miktex_private() -> LatexInstallResult:
    try:
        installer_url = _resolve_miktex_installer_url()
    except Exception as exc:
        return LatexInstallResult(
            success=False,
            message=f"Could not resolve MiKTeX installer URL: {exc}",
            command="",
            engine_path="",
        )

    download_dir = Path(tempfile.gettempdir()) / "jianli-creator-miktex"
    download_dir.mkdir(parents=True, exist_ok=True)
    installer_path = download_dir / installer_url.rsplit("/", 1)[-1]

    try:
        request.urlretrieve(installer_url, installer_path)
    except Exception as exc:
        return LatexInstallResult(
            success=False,
            message=f"Could not download MiKTeX installer: {exc}",
            command=installer_url,
            engine_path="",
        )

    command = f"\"{installer_path}\" --unattended --private"
    completed = subprocess.run(
        [str(installer_path), "--unattended", "--private"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    engine = detect_latex_engine() or _guess_user_engine_path()
    if completed.returncode == 0 and engine:
        return LatexInstallResult(
            success=True,
            message="MiKTeX private installation completed successfully.",
            command=command,
            engine_path=engine,
        )

    output = "\n".join(part for part in [completed.stdout, completed.stderr] if part).strip()
    return LatexInstallResult(
        success=False,
        message=f"MiKTeX private installation did not complete successfully.\n{output}",
        command=command,
        engine_path=engine,
    )


def _install_with_chocolatey() -> LatexInstallResult:
    if not shutil.which("choco"):
        return LatexInstallResult(
            success=False,
            message="Chocolatey is not installed. Install Chocolatey first, then rerun this command.",
            command="",
            engine_path="",
        )

    command = "choco install miktex -y"
    completed = subprocess.run(
        ["choco", "install", "miktex", "-y"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    engine = detect_latex_engine() or _guess_user_engine_path()
    if completed.returncode == 0 and engine:
        return LatexInstallResult(
            success=True,
            message="MiKTeX installed successfully via Chocolatey.",
            command=command,
            engine_path=engine,
        )

    output = "\n".join(part for part in [completed.stdout, completed.stderr] if part).strip()
    return LatexInstallResult(
        success=False,
        message=f"MiKTeX installation via Chocolatey did not complete successfully.\n{output}",
        command=command,
        engine_path=engine,
    )


def _resolve_miktex_installer_url() -> str:
    with request.urlopen(MIKTEX_DOWNLOAD_PAGE, timeout=30) as response:
        html = response.read().decode("utf-8", errors="replace")

    match = re.search(
        r"/download/ctan/systems/win32/miktex/setup/windows-x64/basic-miktex-[^\"' ]+-x64\.exe",
        html,
    )
    if not match:
        raise RuntimeError("Could not find the Basic MiKTeX installer link on the official download page.")
    return urljoin(MIKTEX_DOWNLOAD_PAGE, match.group(0))


def _guess_user_engine_path() -> str:
    local_app_data = os.getenv("LOCALAPPDATA", "")
    if not local_app_data:
        return ""

    roots = [
        Path(local_app_data) / "Programs" / "MiKTeX" / "miktex" / "bin" / "x64",
        Path(local_app_data) / "Programs" / "MiKTeX" / "miktex" / "bin",
    ]
    for root in roots:
        for candidate in ("xelatex.exe", "pdflatex.exe"):
            path = root / candidate
            if path.exists():
                return str(path)
    return ""
