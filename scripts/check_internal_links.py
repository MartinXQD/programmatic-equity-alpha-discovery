"""Check Markdown targets against exact local and committed repository paths.

Remote verification requires an authenticated, freshly fetched Git ref. External
HTTP checks are optional and reported separately; they never replace Git checks.
"""
from __future__ import annotations

import argparse
import html
import json
import posixpath
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO_URL = "https://github.com/MartinXQD/programmatic-equity-alpha-discovery"
ROOT = Path(__file__).resolve().parents[1]


def without_code(text):
    """Ignore fenced examples and inline code, preserving line numbering."""
    lines = []
    fence = None
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^\s{0,3}(" + chr(96) + r"{3,}|~{3,})", line)
        if marker and fence is None:
            fence = marker.group(1)[0]
            lines.append("\n")
        elif fence:
            if marker and marker.group(1)[0] == fence:
                fence = None
            lines.append("\n")
        else:
            lines.append(line)
    return re.sub(chr(96) + r"+[^\n]*?" + chr(96) + r"+", "", "".join(lines))


def destinations(text):
    """Read inline, reference, image, autolink and HTML link destinations."""
    text = without_code(text)
    references = {}
    normalize = lambda s: " ".join(s.casefold().split())
    for m in re.finditer(r"(?m)^\s{0,3}\[([^\]\n]+)\]:\s*(<[^>]+>|\S+)", text):
        references[normalize(m.group(1))] = m.group(2).strip("<>")
    text = re.sub(r"(?m)^\s{0,3}\[[^\]\n]+\]:[^\n]*", "", text)
    spans = []
    for m in re.finditer(r"!?\[[^\]\n]*\]\(", text):
        start = m.end()
        i, depth, escaped = start, 1, False
        while i < len(text) and depth:
            ch = text[i]
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            i += 1
        if depth:
            raise ValueError("Unclosed Markdown link")
        body = text[start:i - 1].strip()
        destination = re.match(r"<([^>]+)>|([^\s]+)", body)
        if destination:
            spans.append((m.start(), i))
            yield html.unescape(re.sub(r"\\([() ])", r"\1", destination.group(1) or destination.group(2)))
    for m in re.finditer(r"!?\[([^\]\n]+)\](?:\[([^\]\n]*)\])?", text):
        if any(a <= m.start() < b for a, b in spans):
            continue
        key = normalize(m.group(2) or m.group(1))
        if key in references:
            yield html.unescape(references[key])
    for m in re.finditer(r"(?:href|src)\s*=\s*([\"'])(.*?)\1", text, re.I):
        yield html.unescape(m.group(2))
    for m in re.finditer(r"<(https?://[^<>\s]+)>", text):
        yield html.unescape(m.group(1))


def classify(source, destination, repo_url=REPO_URL):
    parsed = urllib.parse.urlsplit(destination)
    if parsed.scheme or parsed.netloc:
        prefix = repo_url.rstrip("/") + "/"
        if destination.startswith(prefix):
            suffix = destination[len(prefix):]
            for kind in ("blob/main/", "tree/main/"):
                if suffix.startswith(kind):
                    parsed = urllib.parse.urlsplit(suffix[len(kind):])
                    return "internal", posixpath.normpath(urllib.parse.unquote(parsed.path)), urllib.parse.unquote(parsed.fragment)
        return "external", destination, ""
    path = urllib.parse.unquote(parsed.path)
    if path.startswith("/"):
        target = posixpath.normpath(path.lstrip("/"))
    elif path:
        target = posixpath.normpath(posixpath.join(posixpath.dirname(source), path))
    else:
        target = source
    return "internal", target, urllib.parse.unquote(parsed.fragment)


def in_tree(target, paths):
    return target in paths or target == "." or any(p.startswith(target.rstrip("/") + "/") for p in paths)


def anchors(text):
    result, counts = set(), {}
    text = without_code(text)
    for m in re.finditer(r"(?m)^\s{0,3}#{1,6}\s+(.+?)(?:\s+#+)?\s*$", text):
        title = re.sub(r"<[^>]*>|[\*_]", "", html.unescape(m.group(1))).strip().lower()
        slug = "".join(c for c in title if c.isalnum() or c in "- _").replace(" ", "-")
        n = counts.get(slug, 0)
        counts[slug] = n + 1
        result.add(slug + (f"-{n}" if n else ""))
    result.update(re.findall(r"(?:id|name)=[\"']([^\"']+)[\"']", text))
    return result


def git_paths(root, ref=None):
    command = ["git", "ls-tree", "-r", "--name-only", "-z", ref] if ref else ["git", "ls-files", "-z"]
    return set(subprocess.check_output(command, cwd=root).decode().split("\0")) - {""}


def audit(root, tracked, remote=None, ref=None, remote_ref=None, repo_url=REPO_URL):
    records, external, errors = [], [], []
    for source in sorted(p for p in tracked if p.endswith(".md")):
        text = subprocess.check_output(["git", "show", f"{ref}:{source}"], cwd=root).decode() if ref else (root / source).read_text()
        for destination in destinations(text):
            kind, target, fragment = classify(source, destination, repo_url)
            if kind == "external":
                external.append({"source": source, "url": target, "status": "NOT_CHECKED"})
                continue
            record = {"source": source, "destination": destination, "target": target}
            outside = target == ".." or target.startswith("../")
            local = not outside and in_tree(target, tracked) and (root / target).exists()
            record["local"] = "PASS" if local else "FAIL"
            record["remote"] = "NOT_CHECKED" if remote is None else ("PASS" if not outside and in_tree(target, remote) else "FAIL")
            if fragment and target.endswith(".md") and local:
                target_text = subprocess.check_output(["git", "show", f"{ref}:{target}"], cwd=root).decode() if ref else (root / target).read_text()
                record["anchor"] = "PASS" if fragment in anchors(target_text) else "FAIL"
                if remote_ref and record["remote"] == "PASS":
                    remote_text = subprocess.check_output(["git", "show", f"{remote_ref}:{target}"], cwd=root).decode()
                    record["remote_anchor"] = "PASS" if fragment in anchors(remote_text) else "FAIL"
            if "FAIL" in record.values():
                errors.append(record)
            records.append(record)
    readme_records = [r for r in records if r["source"] in {"README.md", "README_CN.md"}]
    return {"local_ref": ref or "INDEX", "remote_ref": remote_ref,
            "markdown_files": sum(p.endswith(".md") for p in tracked),
            "local_tracked_files": len(tracked), "remote_files": None if remote is None else len(remote),
            "readme_internal_links": len(readme_records), "internal_links": len(records),
            "unique_internal_targets": len({r["target"] for r in records}),
            "verified_working_links": sum(r["local"] == "PASS" and r["remote"] == "PASS" and r.get("anchor", "PASS") == "PASS" and r.get("remote_anchor", "PASS") == "PASS" for r in records),
            "broken_links": len(errors), "errors": errors, "links": records, "external_links": external}


def check_external(records):
    for record in records:
        request = urllib.request.Request(record["url"], headers={"User-Agent": "research-link-audit/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                record.update(status="PASS", http_status=response.status, final_url=response.url)
        except urllib.error.HTTPError as exc:
            record.update(status="BROKEN" if exc.code in (404, 410) else "ACCESS_LIMITED", http_status=exc.code)
        except (urllib.error.URLError, TimeoutError) as exc:
            record.update(status="UNVERIFIED", reason=str(exc.reason if hasattr(exc, "reason") else exc))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", help="Local commit to check, for example HEAD; default checks the index")
    parser.add_argument("--remote-ref", help="Authenticated, freshly fetched remote ref, for example origin/main")
    parser.add_argument("--output", type=Path, help="Write a detailed JSON audit outside the publication whitelist")
    parser.add_argument("--check-external", action="store_true", help="Separately request external URLs without credentials")
    args = parser.parse_args()
    tracked = git_paths(ROOT, args.ref)
    remote = git_paths(ROOT, args.remote_ref) if args.remote_ref else None
    report = audit(ROOT, tracked, remote, args.ref, args.remote_ref)
    if args.remote_ref:
        report["remote_commit"] = subprocess.check_output(["git", "rev-parse", args.remote_ref], cwd=ROOT).decode().strip()
    if args.check_external:
        check_external(report["external_links"])
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in {"links", "external_links"}}, indent=2))
    if args.remote_ref is None:
        print("Remote targets: NOT CHECKED. Fetch with authentication and pass --remote-ref origin/main.")
    raise SystemExit(1 if report["broken_links"] else 0)


if __name__ == "__main__":
    main()
