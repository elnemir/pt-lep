#!/usr/bin/env python3
"""Fetch offline Debian package bundles for supported Debian releases.

The script builds per-component dependency closures from Debian repositories
and downloads .deb files into files/packages/debian{6..13}/...
"""

from __future__ import annotations

import argparse
import gzip
import lzma
import re
import sys
from collections import deque
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


TARGET_ARCH = "amd64"

RELEASES = {
    "debian6": {"suite": "squeeze", "base_url": "https://archive.debian.org/debian"},
    "debian7": {"suite": "wheezy", "base_url": "https://archive.debian.org/debian"},
    "debian8": {"suite": "jessie", "base_url": "https://archive.debian.org/debian"},
    "debian9": {"suite": "stretch", "base_url": "https://archive.debian.org/debian"},
    "debian10": {"suite": "buster", "base_url": "https://archive.debian.org/debian"},
    "debian11": {"suite": "bullseye", "base_url": "https://deb.debian.org/debian"},
    "debian12": {"suite": "bookworm", "base_url": "https://deb.debian.org/debian"},
    "debian13": {"suite": "trixie", "base_url": "https://deb.debian.org/debian"},
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


def fetch_packages_index(base_url: str, suite: str) -> str:
    errors: list[str] = []
    candidates = (
        (f"{base_url}/dists/{suite}/main/binary-{TARGET_ARCH}/Packages.gz", "gz"),
        (f"{base_url}/dists/{suite}/main/binary-{TARGET_ARCH}/Packages.xz", "xz"),
        (f"{base_url}/dists/{suite}/main/binary-{TARGET_ARCH}/Packages", "plain"),
    )
    for url, fmt in candidates:
        try:
            raw = fetch_bytes(url)
        except (HTTPError, URLError) as exc:
            errors.append(f"{url}: {exc}")
            continue
        if fmt == "gz":
            return gzip.decompress(raw).decode("utf-8", errors="replace")
        if fmt == "xz":
            return lzma.decompress(raw).decode("utf-8", errors="replace")
        return raw.decode("utf-8", errors="replace")
    raise RuntimeError(
        f"Failed to load package index for {suite}. Tried: {'; '.join(errors)}"
    )


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


def process_release(repo_root: Path, rel_dir: str, suite: str, base_url: str) -> None:
    print(
        f"[INFO] Loading index for {rel_dir}: "
        f"{base_url}/dists/{suite}/main/binary-{TARGET_ARCH}/Packages.*"
    )
    index_text = fetch_packages_index(base_url, suite)
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
                download_package(base_url, filename, out_path)
            except (HTTPError, URLError) as exc:
                raise RuntimeError(
                    f"Failed to download {pkg} ({filename}) for {suite}: {exc}"
                ) from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch offline Debian package bundles for PT_LEP_unix role."
    )
    parser.add_argument(
        "--releases",
        default="all",
        help=(
            "Comma-separated release directory names to process "
            "(for example: debian13 or debian11,debian12,debian13). "
            "Use 'all' for every configured release."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    if args.releases == "all":
        selected = list(RELEASES.keys())
    else:
        selected = [item.strip() for item in args.releases.split(",") if item.strip()]
        unknown = [item for item in selected if item not in RELEASES]
        if unknown:
            raise RuntimeError(
                f"Unknown releases: {', '.join(unknown)}. "
                f"Allowed: {', '.join(RELEASES)}"
            )

    for rel_dir in selected:
        cfg = RELEASES[rel_dir]
        process_release(
            repo_root,
            rel_dir,
            suite=cfg["suite"],
            base_url=cfg["base_url"],
        )
    print(
        "[INFO] Debian offline bundles downloaded successfully "
        f"for releases: {', '.join(selected)}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover
        print(f"[ERROR] {exc}", file=sys.stderr)
        raise SystemExit(1)
