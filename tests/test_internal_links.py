"""Prevent local-only or incorrectly resolved documentation from passing release QA."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("release_links", Path(__file__).resolve().parents[1] / "scripts/check_internal_links.py")
links = importlib.util.module_from_spec(spec)
spec.loader.exec_module(links)


def test_nested_images_references_spaces_and_code_examples(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "paper").mkdir()
    (tmp_path / "paper/A (draft).pdf").write_bytes(b"fixture")
    (tmp_path / "docs/guide.md").write_text("![Image](<../paper/A (draft).pdf>)\n[Paper][p]\n[p]: <../paper/A (draft).pdf>\n" + chr(96) * 3 + "\n[Example](missing)\n" + chr(96) * 3)
    tracked = {"docs/guide.md", "paper/A (draft).pdf"}
    report = links.audit(tmp_path, tracked, tracked)
    assert report["internal_links"] == 2
    assert report["verified_working_links"] == 2 and report["broken_links"] == 0


def test_remote_absence_case_mismatch_and_escape_are_failures(tmp_path):
    (tmp_path / "paper").mkdir()
    (tmp_path / "paper/CN.pdf").write_bytes(b"fixture")
    (tmp_path / "README.md").write_text("[Real](paper/CN.pdf)\n[Wrong case](paper/cn.pdf)\n[Escape](../private.csv)")
    tracked = {"README.md", "paper/CN.pdf"}
    report = links.audit(tmp_path, tracked, {"README.md"})
    assert report["broken_links"] == 3 and report["verified_working_links"] == 0
    assert report["links"][0]["local"] == "PASS" and report["links"][0]["remote"] == "FAIL"


def test_directories_same_repository_urls_and_external_separation(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src/core.py").write_text("# synthetic fixture")
    (tmp_path / "README.md").write_text("[Code](src/)\n[Absolute](" + links.REPO_URL + "/blob/main/src/core.py)\n[External](https://example.com)")
    tracked = {"README.md", "src/core.py"}
    report = links.audit(tmp_path, tracked, tracked)
    assert report["verified_working_links"] == 2 and report["broken_links"] == 0
    assert len(report["external_links"]) == 1


def test_fragment_must_be_real(tmp_path):
    (tmp_path / "README.md").write_text("# Overview\n[Good](#overview)\n[Bad](#missing)")
    report = links.audit(tmp_path, {"README.md"}, {"README.md"})
    assert report["broken_links"] == 1
