#!/usr/bin/env python3
"""Fetch offline RPM bundles for CentOS and RedOS-compatible targets."""

from __future__ import annotations

import argparse
import bz2
import gzip
import lzma
import os
import shutil
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict, deque
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


TARGET_ARCHES = {"x86_64", "noarch"}

COMMON_XML_NS = "http://linux.duke.edu/metadata/common"
RPM_XML_NS = "http://linux.duke.edu/metadata/rpm"
REPO_XML_NS = "http://linux.duke.edu/metadata/repo"

COMPONENT_ROOTS = {
    "audit": ["audit"],
    "audispd-plugins": ["audispd-plugins"],
    "rsyslog": ["rsyslog"],
    "misc": ["tar"],
}

# For RedOS the script uses CentOS-compatible bundles by default.
RELEASES = {
    "centos7": {
        "repos": [
            "https://vault.centos.org/7.9.2009/updates/x86_64/",
            "https://vault.centos.org/7.9.2009/os/x86_64/",
            "https://vault.centos.org/7.9.2009/extras/x86_64/",
        ],
    },
    "centos8": {
        "repos": [
            "https://vault.centos.org/8.5.2111/BaseOS/x86_64/os/",
            "https://vault.centos.org/8.5.2111/AppStream/x86_64/os/",
            "https://vault.centos.org/8.5.2111/extras/x86_64/os/",
        ],
    },
    "centos9": {
        "repos": [
            "https://mirror.stream.centos.org/9-stream/BaseOS/x86_64/os/",
            "https://mirror.stream.centos.org/9-stream/AppStream/x86_64/os/",
            "https://mirror.stream.centos.org/9-stream/CRB/x86_64/os/",
        ],
    },
    "centos10": {
        "repos": [
            "https://mirror.stream.centos.org/10-stream/BaseOS/x86_64/os/",
            "https://mirror.stream.centos.org/10-stream/AppStream/x86_64/os/",
            "https://mirror.stream.centos.org/10-stream/CRB/x86_64/os/",
        ],
    },
    "redos7": {"alias_of": "centos7"},
    "redos8": {"alias_of": "centos8"},
    "redos9": {"alias_of": "centos9"},
}


def fetch_bytes(url: str) -> bytes:
    req = Request(url, headers={"User-Agent": "pt-lep-offline-fetcher/1.0"})
    with urlopen(req, timeout=120) as resp:
        return resp.read()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch offline RPM bundles for PT_LEP_unix role."
    )
    parser.add_argument(
        "--releases",
        default="all",
        help=(
            "Comma-separated release directory names to process "
            "(for example: centos9,centos10,redos9). "
            "Use 'all' for every configured release."
        ),
    )
    return parser.parse_args()


def decompress_payload(url: str, payload: bytes) -> bytes:
    if url.endswith(".gz"):
        return gzip.decompress(payload)
    if url.endswith(".bz2"):
        return bz2.decompress(payload)
    if url.endswith(".xz"):
        return lzma.decompress(payload)
    return payload


def load_primary_xml(repo_base: str) -> bytes:
    repomd_url = urljoin(repo_base, "repodata/repomd.xml")
    repomd_raw = fetch_bytes(repomd_url)
    root = ET.fromstring(repomd_raw)
    primary_href = None
    for data in root.findall(f"{{{REPO_XML_NS}}}data"):
        if data.attrib.get("type") != "primary":
            continue
        location = data.find(f"{{{REPO_XML_NS}}}location")
        if location is not None and "href" in location.attrib:
            primary_href = location.attrib["href"]
            break
    if not primary_href:
        raise RuntimeError(f"primary metadata not found in {repomd_url}")
    primary_url = urljoin(repo_base, primary_href)
    primary_raw = fetch_bytes(primary_url)
    return decompress_payload(primary_url, primary_raw)


def parse_primary_packages(primary_xml: bytes, repo_base: str) -> list[dict[str, object]]:
    packages: list[dict[str, object]] = []
    package_tag = f"{{{COMMON_XML_NS}}}package"
    name_tag = f"{{{COMMON_XML_NS}}}name"
    arch_tag = f"{{{COMMON_XML_NS}}}arch"
    location_tag = f"{{{COMMON_XML_NS}}}location"
    format_tag = f"{{{COMMON_XML_NS}}}format"
    provides_tag = f"{{{RPM_XML_NS}}}provides"
    requires_tag = f"{{{RPM_XML_NS}}}requires"
    entry_tag = f"{{{RPM_XML_NS}}}entry"

    for _, elem in ET.iterparse(BytesIO(primary_xml), events=("end",)):
        if elem.tag != package_tag:
            continue
        if elem.attrib.get("type") != "rpm":
            elem.clear()
            continue
        name_elem = elem.find(name_tag)
        arch_elem = elem.find(arch_tag)
        location_elem = elem.find(location_tag)
        if name_elem is None or arch_elem is None or location_elem is None:
            elem.clear()
            continue
        arch = (arch_elem.text or "").strip()
        if arch not in TARGET_ARCHES:
            elem.clear()
            continue
        href = location_elem.attrib.get("href")
        if not href:
            elem.clear()
            continue

        provides: set[str] = set()
        requires: set[str] = set()
        fmt = elem.find(format_tag)
        if fmt is not None:
            provides_elem = fmt.find(provides_tag)
            if provides_elem is not None:
                for entry in provides_elem.findall(entry_tag):
                    prov_name = (entry.attrib.get("name") or "").strip()
                    if prov_name:
                        provides.add(prov_name)
            requires_elem = fmt.find(requires_tag)
            if requires_elem is not None:
                for entry in requires_elem.findall(entry_tag):
                    req_name = (entry.attrib.get("name") or "").strip()
                    if not req_name:
                        continue
                    if req_name.startswith("rpmlib("):
                        continue
                    if req_name.startswith("/"):
                        continue
                    requires.add(req_name)

        pkg_name = (name_elem.text or "").strip()
        if pkg_name:
            provides.add(pkg_name)
            packages.append(
                {
                    "name": pkg_name,
                    "url": urljoin(repo_base, href),
                    "requires": requires,
                    "provides": provides,
                }
            )
        elem.clear()
    return packages


def build_release_index(
    repos: list[str],
) -> tuple[dict[str, dict[str, object]], dict[str, list[str]]]:
    package_by_name: dict[str, dict[str, object]] = {}
    providers: dict[str, list[str]] = defaultdict(list)

    for repo_base in repos:
        print(f"[INFO] Loading RPM metadata: {repo_base}")
        primary_xml = load_primary_xml(repo_base)
        pkg_records = parse_primary_packages(primary_xml, repo_base)
        for rec in pkg_records:
            name = rec["name"]
            if name in package_by_name:
                continue
            package_by_name[name] = rec
            for prov in rec["provides"]:
                if name not in providers[prov]:
                    providers[prov].append(name)

    if not package_by_name:
        raise RuntimeError("Empty package index for configured RPM repos")
    return package_by_name, providers


def resolve_pkg(
    token: str, package_by_name: dict[str, dict[str, object]], providers: dict[str, list[str]]
) -> str | None:
    if token in package_by_name:
        return token
    candidates = providers.get(token)
    if candidates:
        return candidates[0]
    return None


def dependency_closure(
    package_by_name: dict[str, dict[str, object]],
    providers: dict[str, list[str]],
    roots: list[str],
) -> set[str]:
    closure: set[str] = set()
    queue = deque(roots)

    while queue:
        token = queue.popleft()
        pkg_name = resolve_pkg(token, package_by_name, providers)
        if not pkg_name or pkg_name in closure:
            continue
        closure.add(pkg_name)
        rec = package_by_name[pkg_name]
        for req in rec["requires"]:
            if req in closure:
                continue
            queue.append(req)
    return closure


def download_packages(
    release_dir: str,
    component: str,
    closure: set[str],
    package_by_name: dict[str, dict[str, object]],
    repo_root: Path,
) -> None:
    out_dir = repo_root / "files" / "packages" / release_dir / component
    out_dir.mkdir(parents=True, exist_ok=True)

    for pkg_name in sorted(closure):
        rec = package_by_name[pkg_name]
        url = rec["url"]
        dest = out_dir / Path(url).name
        if dest.exists():
            continue
        payload = fetch_bytes(url)
        dest.write_bytes(payload)


def process_release(
    release_dir: str,
    repos: list[str],
    repo_root: Path,
) -> None:
    package_by_name, providers = build_release_index(repos)
    for component, roots in COMPONENT_ROOTS.items():
        closure = dependency_closure(package_by_name, providers, roots)
        if not closure:
            raise RuntimeError(
                f"No packages resolved for {release_dir}/{component} (roots={roots})"
            )
        print(
            f"[INFO] {release_dir}/{component}: resolved {len(closure)} packages from roots {roots}"
        )
        download_packages(release_dir, component, closure, package_by_name, repo_root)


def hardlink_release_alias(repo_root: Path, source: str, target: str) -> None:
    for component in COMPONENT_ROOTS:
        src_dir = repo_root / "files" / "packages" / source / component
        dst_dir = repo_root / "files" / "packages" / target / component
        dst_dir.mkdir(parents=True, exist_ok=True)
        if not src_dir.exists():
            raise RuntimeError(f"Alias source component directory not found: {src_dir}")
        for src_file in sorted(src_dir.glob("*.rpm")):
            dst_file = dst_dir / src_file.name
            if dst_file.exists():
                continue
            try:
                os.link(src_file, dst_file)
            except OSError:
                shutil.copy2(src_file, dst_file)
    print(f"[INFO] {target}: aliased from {source} via hard links/copies")


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
        alias_of = cfg.get("alias_of")
        if alias_of:
            if alias_of not in completed:
                source_cfg = RELEASES.get(alias_of)
                if not source_cfg or "repos" not in source_cfg:
                    raise RuntimeError(f"Alias source {alias_of} is not downloadable")
                process_release(alias_of, source_cfg["repos"], repo_root)
                completed.add(alias_of)
            hardlink_release_alias(repo_root, alias_of, release)
            completed.add(release)
            continue

        process_release(release, cfg["repos"], repo_root)
        completed.add(release)

    print(
        "[INFO] RPM offline bundles downloaded successfully "
        f"for releases: {', '.join(selected)}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover
        print(f"[ERROR] {exc}", file=sys.stderr)
        raise SystemExit(1)
