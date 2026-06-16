"""Offline tests for the self-updater's pure logic and file-copy step.

Network/download paths aren't exercised here — the helpers below are factored so
version selection and the in-place copy can be tested without GitHub.
"""

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_DIR))

import selfupdate  # noqa: E402


def test_parse_version_handles_tag_and_bare_and_junk():
    assert selfupdate.parse_version("job-app-llm-helper-v0.2.5") == (0, 2, 5)
    assert selfupdate.parse_version("v1.10.3") == (1, 10, 3)
    assert selfupdate.parse_version("0.2.4") == (0, 2, 4)
    assert selfupdate.parse_version("job-app-llm-helper-vbeta") is None
    assert selfupdate.parse_version("") is None


def test_is_newer_semantics():
    assert selfupdate.is_newer((0, 2, 5), (0, 2, 4)) is True
    assert selfupdate.is_newer((0, 2, 4), (0, 2, 4)) is False
    assert selfupdate.is_newer((0, 2, 3), (0, 2, 4)) is False
    assert selfupdate.is_newer((1, 0), (0, 9, 9)) is True
    # Unknown local -> treat any remote as newer; unknown remote -> never.
    assert selfupdate.is_newer((0, 1), None) is True
    assert selfupdate.is_newer(None, (0, 1)) is False


def test_pick_latest_filters_prefix_draft_prerelease_and_picks_highest():
    releases = [
        {"tag_name": "job-app-llm-helper-v0.2.3", "assets": [{"name": "a"}]},
        {"tag_name": "job-app-llm-helper-v0.2.5", "assets": [{"name": "b"}]},
        {"tag_name": "job-app-llm-helper-v0.3.0", "prerelease": True, "assets": []},
        {"tag_name": "job-app-llm-helper-v0.2.9", "draft": True, "assets": []},
        {"tag_name": "some-other-project-v9.9.9", "assets": []},
    ]
    tag, ver, assets = selfupdate.pick_latest(releases)
    assert tag == "job-app-llm-helper-v0.2.5"
    assert ver == (0, 2, 5)
    assert assets == [{"name": "b"}]


def test_pick_latest_none_when_nothing_matches():
    assert selfupdate.pick_latest([{"tag_name": "other-v1.0.0"}]) is None
    assert selfupdate.pick_latest([]) is None


def test_find_tarball_url_prefers_targz():
    assets = [
        {"name": "x.zip", "browser_download_url": "ZIP"},
        {"name": "x.tar.gz", "browser_download_url": "TGZ"},
    ]
    assert selfupdate.find_tarball_url(assets) == "TGZ"
    assert selfupdate.find_tarball_url([{"name": "x.zip"}]) is None


def test_payload_root_unwraps_prefixed_dir(tmp_path):
    inner = tmp_path / "job-app-llm-helper"
    inner.mkdir()
    assert selfupdate.payload_root(tmp_path) == inner
    bare = tmp_path / "bare"
    bare.mkdir()
    assert selfupdate.payload_root(bare) == bare


def test_copy_over_overwrites_app_files_but_keeps_venv(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    (src / "sub").mkdir(parents=True)
    (dst / "venv" / "lib").mkdir(parents=True)
    # New payload: an updated app file + a venv dir that must NOT clobber the real one.
    (src / "app.py").write_text("new")
    (src / "sub" / "x.txt").write_text("hi")
    (src / "venv").mkdir()
    (src / "venv" / "SHOULD_NOT_COPY").write_text("bad")
    (dst / "app.py").write_text("old")
    (dst / "venv" / "lib" / "keep.txt").write_text("precious")

    selfupdate._copy_over(src, dst)

    assert (dst / "app.py").read_text() == "new"
    assert (dst / "sub" / "x.txt").read_text() == "hi"
    assert (dst / "venv" / "lib" / "keep.txt").read_text() == "precious"
    assert not (dst / "venv" / "SHOULD_NOT_COPY").exists()


def test_local_version_reads_version_file(tmp_path):
    (tmp_path / "VERSION").write_text("0.2.4\n")
    assert selfupdate.local_version(tmp_path) == (0, 2, 4)
    assert selfupdate.local_version(tmp_path / "nope") is None


def test_shipped_version_file_matches_parse():
    # The repo's VERSION must be parseable, or self-update can't compare.
    assert selfupdate.local_version(APP_DIR) is not None
