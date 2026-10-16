"""Regression tests for scan failures and report preservation."""

import json
import os
from contextlib import contextmanager

import pytest

import game_mod_guard as guard


@pytest.mark.parametrize("kind", ["same", "symlink", "hardlink", "unrelated", "dangling", "new"])
def test_report_never_overwrites_input(tmp_path, kind, capsys):
    source = tmp_path / "mod.lua"
    source.write_text("-- ordinary mod\n")
    destination = tmp_path / "report.json"
    if kind == "same":
        destination = source
    elif kind == "symlink":
        destination.symlink_to(source)
    elif kind == "hardlink":
        os.link(source, destination)
    elif kind == "unrelated":
        destination.write_text("old report")
    elif kind == "dangling":
        destination.symlink_to(tmp_path / "missing")
    before = source.read_bytes()
    old_umask = os.umask(0)
    try:
        code = guard.main(["--no-defender", str(source), "--json", str(destination)])
    finally:
        os.umask(old_umask)
    assert source.read_bytes() == before
    if kind == "new":
        assert code == 0
        assert json.loads(destination.read_text())[0]["verdict"] == "SAFE-LOOKING"
        if os.name == "posix":
            assert destination.stat().st_mode & 0o777 == 0o600
    else:
        assert code == 1
        assert "Report could not be written" in capsys.readouterr().err
        if kind == "unrelated":
            assert destination.read_text() == "old report"
        if kind == "dangling":
            assert not (tmp_path / "missing").exists()


def test_unreadable_tree_is_not_safe(tmp_path, monkeypatch, capsys):
    denied = tmp_path / "denied"
    denied.mkdir()
    original = os.scandir
    def scandir(path):
        if str(path) == str(denied):
            raise PermissionError(13, "fixture denial", str(denied))
        return original(path)
    monkeypatch.setattr(os, "scandir", scandir)
    assert guard.main(["--no-defender", str(tmp_path)]) == 1
    text = capsys.readouterr().out
    assert "SAFE-LOOKING" not in text
    assert "directory inspection incomplete" in text


def test_read_failure_is_review(tmp_path, monkeypatch):
    source = tmp_path / "mod.lua"
    source.write_text("-- ordinary mod")
    def denied(_):
        raise PermissionError("fixture denial")
    monkeypatch.setattr(guard, "sha256_file", denied)
    report = guard.scan_target(source, defender=False)
    assert report.verdict == "REVIEW"
    assert any(f.issue == "file inspection incomplete" for f in report.findings)


def test_missing_metadata_does_not_downgrade_executable_finding(tmp_path, monkeypatch):
    source = tmp_path / "install.exe"
    source.write_text("inert fixture")
    original = type(source).stat
    def denied(path, *args, **kwargs):
        if path == source:
            raise PermissionError("fixture denial")
        return original(path, *args, **kwargs)
    monkeypatch.setattr(type(source), "stat", denied)
    report = guard.scan_target(tmp_path, defender=False)
    assert report.verdict == "STOP"
    assert any(f.issue == "file inspection incomplete" for f in report.findings)


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="POSIX special file")
def test_special_file_does_not_block(tmp_path):
    source = tmp_path / "pipe"
    os.mkfifo(source)
    assert guard.scan_target(source, defender=False).verdict == "REVIEW"


def test_partial_report_write_fails(tmp_path, monkeypatch, capsys):
    source = tmp_path / "mod.lua"
    source.write_text("-- ordinary mod")
    original = os.fdopen
    closed = []
    @contextmanager
    def failing_writer(fd, *args, **kwargs):
        with original(fd, *args, **kwargs) as handle:
            class Writer:
                def write(self, data):
                    handle.write(data[:4])
                    raise OSError("fixture write failure")
            try:
                yield Writer()
            finally:
                closed.append(fd)
    monkeypatch.setattr(os, "fdopen", failing_writer)
    assert guard.main(["--no-defender", str(source), "--json", str(tmp_path / "new.json")]) == 1
    assert "fixture write failure" in capsys.readouterr().err
    assert source.read_text() == "-- ordinary mod"
    with pytest.raises(OSError):
        os.fstat(closed[0])

