#!/usr/bin/env python3
"""Fetch offline Debian package bundles for legacy releases.

This script builds per-component dependency closures from archive.debian.org
and downloads .deb files into files/packages/debian{6,7,8}/...
"""

from __future__ import annotations

import gzip
import re
import sys
from collections import deque
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = "https://archive.debian.org/debian"
TARGET_ARCH = "amd64"

RELEASES = {
    "debian6": "squeeze",
    "debian7": "wheezy",
    "debian8": "jessie",
}

COMPONENT_ROOTS = {
    "auditd": ["auditd"],
    "audispd-plugins": ["audispd-plugins"],
    "rsyslog": ["rsyslog"],
    "misc": ["tar"],
}


def fetch_bytes(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": "pt-lep-offline-fetcher/1.0"})
    with urlopen(req, timeout=60) as resp:
        return resp.read()


def parse_packages_index(data: str) -> dict[str, dict[str, str]]:
    records: dict[str, dict[str, str]] = {}
    for stanza in data.split("\n\n"):
        if not stanza.strip():
            continue
        fields: dict[str, str] = {}
        current_key = None
        for line in stanza.splitlines():
            if not line:
                continue
            if line.startswith(" ") and current_key:
                fields[current_key] += " " + line.strip()
                continue
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip()
            fields[key] = value.strip()
            current_key = key

        pkg = fields.get("Package")
        arch = fields.get("Architecture")
        filename = fields.get("Filename")
        if not pkg or not arch or not filename:
            continue
        if arch not in (TARGET_ARCH, "all"):
            continue
        # Keep the first occurrence (archive indexes are typically single-version)
        records.setdefault(pkg, fields)
    return records


_dep_token_re = re.compile(r"^\s*([a-zA-Z0-9.+-]+)")


def parse_dep_candidates(dep_expr: str) -> list[str]:
    result: list[str] = []
    for raw_item in dep_expr.split(","):
        alternatives = raw_item.split("|")
        candidates: list[str] = []
        for alt in alternatives:
            alt = alt.strip()
            if not alt:
                continue
            alt = re.sub(r"\s*\(.*?\)", "", alt)
            alt = re.sub(r":[a-z0-9-]+", "", alt)
            m = _dep_token_re.match(alt)
            if m:
                candidates.append(m.group(1))
        if candidates:
            result.append(candidates[0])
    return result


def dependency_closure(index: dict[str, dict[str, str]], roots: list[str]) -> set[str]:
    closure: set[str] = set()
    queue = deque(roots)
    while queue:
        pkg = queue.popleft()
        if pkg in closure:
            continue
        if pkg not in index:
            # keep going: virtual or unavailable package
            continue
        closure.add(pkg)
        rec = index[pkg]
        dep_exprs = []
        if "Pre-Depends" in rec:
            dep_exprs.append(rec["Pre-Depends"])
        if "Depends" in rec:
            dep_exprs.append(rec["Depends"])
        for dep_expr in dep_exprs:
            for dep in parse_dep_candidates(dep_expr):
                if dep not in closure:
                    queue.append(dep)
    return closure


def download_package(base_url: str, filename: str, out_path: Path) -> None:
    if out_path.exists():
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = fetch_bytes(f"{base_url}/{filename}")
    out_path.write_bytes(payload)


def process_release(repo_root: Path, rel_dir: str, suite: str) -> None:
    index_url = f"{BASE_URL}/dists/{suite}/main/binary-{TARGET_ARCH}/Packages.gz"
    print(f"[INFO] Loading index: {index_url}")
    index_raw = fetch_bytes(index_url)
    index_text = gzip.decompress(index_raw).decode("utf-8", errors="replace")
    index = parse_packages_index(index_text)
    if not index:
        raise RuntimeError(f"Empty package index for {suite}")

    for component, roots in COMPONENT_ROOTS.items():
        closure = dependency_closure(index, roots)
        if not closure:
            raise RuntimeError(
                f"No packages resolved for {suite}/{component} (roots={roots})"
            )
        print(
            f"[INFO] {rel_dir}/{component}: resolved {len(closure)} packages from roots {roots}"
        )
        out_dir = repo_root / "files" / "packages" / rel_dir / component
        for pkg in sorted(closure):
            rec = index.get(pkg)
            if not rec:
                continue
            filename = rec["Filename"]
            out_path = out_dir / Path(filename).name
            try:
                download_package(BASE_URL, filename, out_path)
            except (HTTPError, URLError) as exc:
                raise RuntimeError(
                    f"Failed to download {pkg} ({filename}) for {suite}: {exc}"
                ) from exc


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    for rel_dir, suite in RELEASES.items():
        process_release(repo_root, rel_dir, suite)
    print("[INFO] Legacy Debian offline bundles downloaded successfully.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover
        print(f"[ERROR] {exc}", file=sys.stderr)
        raise SystemExit(1)
