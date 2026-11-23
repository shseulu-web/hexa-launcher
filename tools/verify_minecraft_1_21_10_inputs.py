#!/usr/bin/env python3
"""Verify Mojang's official 1.21.10 metadata and mapping downloads without publishing game files."""

import hashlib
import json
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
TARGET = "1.21.10"
REQUIRED = ("client", "client_mappings", "server", "server_mappings")


def get_json(url):
    request = urllib.request.Request(url, headers={"User-Agent": "HexaLauncher-1.21.10-input-audit/1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def verify_download(label, item, workdir, converter):
    url = item.get("url", "")
    expected = item.get("sha1", "")
    size = item.get("size")
    if not url.startswith("https://") or not re.fullmatch(r"[0-9a-f]{40}", expected):
        raise ValueError(f"{label}: invalid official URL or SHA-1 metadata")
    if not isinstance(size, int) or size <= 0:
        raise ValueError(f"{label}: invalid official file size")

    mapping_path = workdir / f"{label}.pro"
    tiny_path = workdir / f"{label}.tiny"
    digest = hashlib.sha1()
    received = 0
    request = urllib.request.Request(url, headers={"User-Agent": "HexaLauncher-1.21.10-input-audit/1"})
    with urllib.request.urlopen(request, timeout=120) as response, mapping_path.open("wb") as output:
        while True:
            block = response.read(1024 * 1024)
            if not block:
                break
            received += len(block)
            digest.update(block)
            output.write(block)
    actual = digest.hexdigest()
    if received != size or actual != expected:
        raise ValueError(f"{label}: size/SHA-1 mismatch (bytes={received}, sha1={actual})")

    subprocess.run(
        [sys.executable, str(converter), "--input", str(mapping_path), "--output", str(tiny_path)],
        check=True,
    )
    tiny_lines = tiny_path.read_text(encoding="utf-8").splitlines()
    return {
        "bytes": received,
        "sha1": actual,
        "tiny_sha256": hashlib.sha256(tiny_path.read_bytes()).hexdigest(),
        "class_count": sum(line.startswith("c\\t") for line in tiny_lines),
        "member_count": sum(line.startswith("\\tf\\t") or line.startswith("\\tm\\t") for line in tiny_lines),
    }


def main():
    manifest = get_json(MANIFEST_URL)
    version = next((entry for entry in manifest["versions"] if entry["id"] == TARGET), None)
    if version is None or version.get("type") != "release":
        raise ValueError(f"Mojang version manifest does not list {TARGET} as a release")
    metadata = get_json(version["url"])
    if metadata.get("id") != TARGET:
        raise ValueError(f"Version metadata ID mismatch: {metadata.get('id')!r}")
    java_major = metadata.get("javaVersion", {}).get("majorVersion")
    if java_major != 21:
        raise ValueError(f"Expected Minecraft {TARGET} Java 21 metadata, got {java_major!r}")
    downloads = metadata.get("downloads", {})
    missing = [name for name in REQUIRED if name not in downloads]
    if missing:
        raise ValueError(f"Mojang metadata is missing required official artifacts: {', '.join(missing)}")

    verified = {}
    converter = Path(__file__).resolve().with_name("proguard_to_tiny.py")
    with tempfile.TemporaryDirectory(prefix="hexa-1.21.10-mappings-") as temporary:
        workdir = Path(temporary)
        for name in ("client_mappings", "server_mappings"):
            verified[name] = verify_download(name, downloads[name], workdir, converter)

    print(json.dumps({
        "version": TARGET,
        "java_major": java_major,
        "metadata_url": version["url"],
        "official_mapping_artifacts": verified,
        "game_jars": "present in Mojang metadata; not downloaded or redistributed by this audit",
        "result": "PASS",
    }, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (KeyError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"1.21.10 input audit failed: {error}", file=sys.stderr)
        sys.exit(1)
