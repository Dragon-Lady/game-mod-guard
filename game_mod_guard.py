#!/usr/bin/env python3
"""Read-only safety checker for downloaded game mods.

The scanner intentionally avoids extraction-by-default. It reads archive
metadata, hashes input files, optionally invokes Microsoft Defender on Windows,
and reports review guidance without deleting or modifying the target.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable


__version__ = "0.1.1"

ARCHIVE_EXTENSIONS = {".zip", ".scs"}
NESTED_ARCHIVE_EXTENSIONS = {
    ".zip",
    ".rar",
    ".7z",
    ".tar",
    ".gz",
    ".bz2",
    ".xz",
    ".cab",
    ".iso",
}
STOP_EXTENSIONS = {
    ".exe",
    ".msi",
    ".scr",
    ".com",
    ".pif",
    ".cpl",
    ".hta",
    ".jar",
    ".lnk",
}
REVIEW_EXTENSIONS = {
    ".bat",
    ".cmd",
    ".ps1",
    ".psm1",
    ".vbs",
    ".vbe",
    ".js",
    ".jse",
    ".wsf",
    ".wsh",
    ".dll",
    ".sys",
    ".reg",
    ".url",
}
EXPECTED_MOD_EXTENSIONS = {
    ".dds",
    ".i3d",
    ".xml",
    ".mat",
    ".png",
    ".jpg",
    ".jpeg",
    ".ogg",
    ".wav",
    ".mp3",
    ".sii",
    ".sui",
    ".tobj",
    ".pmd",
    ".pmg",
    ".pmc",
    ".txt",
    ".lua",
    ".json",
    ".csv",
}
MAX_ARCHIVE_BYTES = 2 * 1024 * 1024 * 1024


@dataclass
class Finding:
    severity: str
    path: str
    issue: str
    detail: str = ""


@dataclass
class TargetReport:
    path: str
    exists: bool
    kind: str = "missing"
    size: int | None = None
    sha256: str | None = None
    defender_status: str = "not-run"
    defender_detail: str = ""
    findings: list[Finding] = field(default_factory=list)

    @property
    def verdict(self) -> str:
        severities = {f.severity for f in self.findings}
        if "STOP" in severities:
            return "STOP"
        if "REVIEW" in severities or not self.exists:
            return "REVIEW"
        return "SAFE-LOOKING"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def classify_name(name: str) -> tuple[str | None, str]:
    lowered = name.lower().replace("\\", "/")
    suffix = Path(lowered).suffix
    if lowered.startswith("__macosx/") or lowered.endswith("/"):
        return None, ""
    if suffix in STOP_EXTENSIONS:
        return "STOP", f"executable-style file: {suffix}"
    if suffix in REVIEW_EXTENSIONS:
        return "REVIEW", f"script/system file: {suffix}"
    if suffix in NESTED_ARCHIVE_EXTENSIONS:
        return "REVIEW", f"nested archive: {suffix}"
    if suffix and suffix not in EXPECTED_MOD_EXTENSIONS:
        return "REVIEW", f"unusual file type: {suffix}"
    return None, ""


def inspect_zip(path: Path, report: TargetReport) -> None:
    if report.size is not None and report.size > MAX_ARCHIVE_BYTES:
        report.findings.append(
            Finding(
                "REVIEW",
                str(path),
                "very large archive",
                "Large mod archives are not automatically bad, but they deserve review.",
            )
        )
    try:
        with zipfile.ZipFile(path) as zf:
            bad_zip = zf.testzip()
            if bad_zip:
                report.findings.append(
                    Finding("REVIEW", bad_zip, "archive integrity warning")
                )
            for info in zf.infolist():
                if info.flag_bits & 0x1:
                    report.findings.append(
                        Finding(
                            "REVIEW",
                            info.filename,
                            "password-protected archive entry",
                            "Do not install password-protected mods from random sites.",
                        )
                    )
                severity, issue = classify_name(info.filename)
                if severity:
                    report.findings.append(
                        Finding(severity, info.filename, issue, f"{info.file_size} bytes")
                    )
    except zipfile.BadZipFile:
        report.findings.append(
            Finding(
                "REVIEW",
                str(path),
                "archive could not be read as zip/scs",
                "The file may be corrupt, encrypted, password-protected, or not a normal zip archive.",
            )
        )
    except RuntimeError as exc:
        report.findings.append(
            Finding(
                "REVIEW",
                str(path),
                "archive could not be fully inspected",
                str(exc),
            )
        )


def inspect_regular_file(path: Path, report: TargetReport) -> None:
    severity, issue = classify_name(path.name)
    if severity:
        report.findings.append(Finding(severity, str(path), issue))


def inspect_directory(path: Path, report: TargetReport) -> None:
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in {".git", "__pycache__"}]
        for filename in files:
            file_path = Path(root) / filename
            rel = str(file_path.relative_to(path))
            severity, issue = classify_name(rel)
            if severity:
                try:
                    size = file_path.stat().st_size
                except OSError:
                    size = 0
                report.findings.append(Finding(severity, rel, issue, f"{size} bytes"))


def find_defender() -> Path | None:
    if platform.system().lower() != "windows":
        return None
    candidates = [
        Path(os.environ.get("ProgramFiles", "")) / "Windows Defender" / "MpCmdRun.exe",
        Path(os.environ.get("ProgramData", ""))
        / "Microsoft"
        / "Windows Defender"
        / "Platform",
    ]
    exe = candidates[0]
    if exe.exists():
        return exe
    platform_dir = candidates[1]
    if platform_dir.exists():
        versions = sorted(platform_dir.glob("*/MpCmdRun.exe"), reverse=True)
        if versions:
            return versions[0]
    found = shutil.which("MpCmdRun.exe")
    return Path(found) if found else None


def run_defender(path: Path, report: TargetReport) -> None:
    defender = find_defender()
    if not defender:
        report.defender_status = "unavailable"
        return
    cmd = [
        str(defender),
        "-Scan",
        "-ScanType",
        "3",
        "-File",
        str(path),
        "-DisableRemediation",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except Exception as exc:
        report.defender_status = "error"
        report.defender_detail = str(exc)
        report.findings.append(
            Finding("REVIEW", str(path), "Defender scan did not complete", str(exc))
        )
        return
    report.defender_detail = (proc.stdout + "\n" + proc.stderr).strip()[-2000:]
    if proc.returncode == 0:
        report.defender_status = "clean"
    else:
        report.defender_status = f"exit-{proc.returncode}"
        report.findings.append(
            Finding(
                "STOP",
                str(path),
                "Microsoft Defender reported a problem or scan error",
                f"exit code {proc.returncode}",
            )
        )


def scan_target(path: Path, defender: bool) -> TargetReport:
    report = TargetReport(path=str(path), exists=path.exists())
    if not path.exists():
        report.findings.append(Finding("REVIEW", str(path), "path does not exist"))
        return report

    if path.is_dir():
        report.kind = "directory"
        inspect_directory(path, report)
    else:
        report.kind = "file"
        report.size = path.stat().st_size
        report.sha256 = sha256_file(path)
        if path.suffix.lower() in ARCHIVE_EXTENSIONS:
            report.kind = "archive"
            inspect_zip(path, report)
        else:
            inspect_regular_file(path, report)

    if defender:
        run_defender(path, report)
    return report


def print_report(report: TargetReport) -> None:
    print(f"\n== {report.verdict}: {report.path}")
    print(f"kind: {report.kind}")
    if report.size is not None:
        print(f"size: {report.size} bytes")
    if report.sha256:
        print(f"sha256: {report.sha256}")
    print(f"defender: {report.defender_status}")
    if not report.findings:
        print("findings: none")
    else:
        print("findings:")
        for finding in report.findings:
            detail = f" ({finding.detail})" if finding.detail else ""
            print(f"  - [{finding.severity}] {finding.path}: {finding.issue}{detail}")
    if report.verdict == "STOP":
        print("action: do not install. Delete the downloaded mod and get it from a safer source.")
    elif report.verdict == "REVIEW":
        print("action: ask a technical friend to review before installing.")
    else:
        print("action: safe-looking, but still prefer official/trusted mod sources.")


def json_ready(reports: Iterable[TargetReport]) -> list[dict]:
    out = []
    for report in reports:
        item = asdict(report)
        item["verdict"] = report.verdict
        out.append(item)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only safety checker for downloaded game mods."
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"game-mod-guard {__version__}",
    )
    parser.add_argument("targets", nargs="+", help="Mod file, archive, or folder to scan")
    parser.add_argument(
        "--no-defender",
        action="store_true",
        help="Skip Microsoft Defender scan even when available",
    )
    parser.add_argument("--json", help="Write JSON report to this path")
    args = parser.parse_args(argv)

    reports = [scan_target(Path(t), defender=not args.no_defender) for t in args.targets]
    for report in reports:
        print_report(report)

    if args.json:
        Path(args.json).write_text(json.dumps(json_ready(reports), indent=2), encoding="utf-8")
        print(f"\nJSON report written: {args.json}")

    return 2 if any(r.verdict == "STOP" for r in reports) else 1 if any(r.verdict == "REVIEW" for r in reports) else 0


if __name__ == "__main__":
    raise SystemExit(main())
