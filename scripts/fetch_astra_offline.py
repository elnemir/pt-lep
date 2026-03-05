#!/usr/bin/env python3
"""Fetch offline AstraLinux package bundles for supported Astra releases.

The script downloads native bundles from public Astra frozen repositories where
full package indexes are available and builds compatibility aliases for legacy
releases that do not expose a full public repository.
"""

from __future__ import annotations

import argparse
import gzip
import lzma
import os
import shutil
import re
import sys
from collections import deque
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


TARGET_ARCH = "amd64"

COMPONENTS = ("main", "contrib", "non-free")

COMPONENT_ROOTS = {
    "auditd": ["auditd"],
    "audispd-plugins": ["audispd-plugins"],
    "rsyslog": ["rsyslog"],
    "misc": ["tar"],
}

RELEASES: dict[str, dict[str, object]] = {
    "astra111": {
        "type": "apt",
        "suite": "orel",
        "base_url": "https://dl.astralinux.ru/astra/frozen/1.11_x86-64-ce/repository",
    },
    "astra212": {
        "type": "apt",
        "suite": "orel",
        "base_url": "https://dl.astralinux.ru/astra/frozen/2.12_x86-64/2.12.46/repository",
    },
    # Legacy Astra branches do not expose full public package indexes.
    # They intentionally reuse already prepared compatibility bundles.
    "astra15": {"type": "alias", "alias_of": "debian9"},
    "astra16": {"type": "alias", "alias_of": "debian9"},
    "astra17": {"type": "alias", "alias_of": "astra111"},
    "astra18": {"type": "alias", "alias_of": "debian12"},
}


def fetch_bytes(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": "pt-lep-offline-fetcher/1.0"})
    with urlopen(req, timeout=120) as resp:
        return resp.read()


def fetch_packages_index(base_url: str, suite: str, component: str) -> str:
    errors: list[str] = []
    candidates = (
        (
            f"{base_url}/dists/{suite}/{component}/binary-{TARGET_ARCH}/Packages.gz",
            "gz",
        ),
        (
            f"{base_url}/dists/{suite}/{component}/binary-{TARGET_ARCH}/Packages.xz",
            "xz",
        ),
        (f"{base_url}/dists/{suite}/{component}/binary-{TARGET_ARCH}/Packages", "plain"),
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
        f"Failed to load package index for {suite}/{component}. Tried: {'; '.join(errors)}"
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
        # Prefer packages with newer versions if seen in multiple components.
        records[pkg] = fields
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
        rec = index.get(pkg)
        if not rec:
            continue
        closure.add(pkg)
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


def build_merged_index(base_url: str, suite: str) -> dict[str, dict[str, str]]:
    merged: dict[str, dict[str, str]] = {}
    for component in COMPONENTS:
        try:
            idx_text = fetch_packages_index(base_url, suite, component)
        except RuntimeError:
            continue
        parsed = parse_packages_index(idx_text)
        merged.update(parsed)
    if not merged:
        raise RuntimeError(f"Empty package index for {base_url} suite={suite}")
    return merged


def process_apt_release(
    repo_root: Path,
    rel_dir: str,
    suite: str,
    base_url: str,
) -> None:
    print(
        f"[INFO] Loading Astra index for {rel_dir}: "
        f"{base_url}/dists/{suite}/{{main,contrib,non-free}}/binary-{TARGET_ARCH}/Packages.*"
    )
    index = build_merged_index(base_url, suite)

    for component, roots in COMPONENT_ROOTS.items():
        closure = dependency_closure(index, roots)
        if not closure:
            raise RuntimeError(
                f"No packages resolved for {rel_dir}/{component} (roots={roots})"
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
                    f"Failed to download {pkg} ({filename}) for {rel_dir}: {exc}"
                ) from exc


def hardlink_release_alias(repo_root: Path, source: str, target: str) -> None:
    for component in COMPONENT_ROOTS:
        src_dir = repo_root / "files" / "packages" / source / component
        dst_dir = repo_root / "files" / "packages" / target / component
        dst_dir.mkdir(parents=True, exist_ok=True)
        if not src_dir.exists():
            raise RuntimeError(f"Alias source component directory not found: {src_dir}")
        for src_file in sorted(src_dir.glob("*.deb")):
            dst_file = dst_dir / src_file.name
            if dst_file.exists():
                continue
            try:
                os.link(src_file, dst_file)
            except OSError:
                shutil.copy2(src_file, dst_file)
    print(f"[INFO] {target}: aliased from {source} via hard links/copies")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch offline AstraLinux package bundles for PT_LEP_unix role."
    )
    parser.add_argument(
        "--releases",
        default="all",
        help=(
            "Comma-separated release directory names to process "
            "(for example: astra111,astra212 or astra15,astra16). "
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
                f"Unknown releases: {', '.join(unknown)}. Allowed: {', '.join(RELEASES)}"
            )

    completed: set[str] = set()
    for release in selected:
        cfg = RELEASES[release]
        release_type = cfg.get("type")
        if release_type == "alias":
            source = str(cfg["alias_of"])
            if source in RELEASES and source not in completed:
                source_cfg = RELEASES[source]
                if source_cfg.get("type") != "apt":
                    raise RuntimeError(f"Alias source {source} is not downloadable")
                process_apt_release(
                    repo_root,
                    source,
                    suite=str(source_cfg["suite"]),
                    base_url=str(source_cfg["base_url"]),
                )
                completed.add(source)
            hardlink_release_alias(repo_root, source, release)
            completed.add(release)
            continue

        if release_type != "apt":
            raise RuntimeError(f"Unsupported release type for {release}: {release_type}")

        process_apt_release(
            repo_root,
            release,
            suite=str(cfg["suite"]),
            base_url=str(cfg["base_url"]),
        )
        completed.add(release)

    print(
        "[INFO] Astra offline bundles downloaded/aliased successfully "
        f"for releases: {', '.join(selected)}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover
        print(f"[ERROR] {exc}", file=sys.stderr)
        raise SystemExit(1)
