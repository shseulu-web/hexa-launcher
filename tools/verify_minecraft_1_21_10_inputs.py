#!/usr/bin/env python3
"""Verify Mojang's official 1.21.10 metadata and mapping downloads without publishing game files."""

import hashlib
import json
import re
import sys
import urllib.request

MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
TARGET = "1.21.10"
REQUIRED = ("client", "client_mappings", "server", "server_mappings")


def get_json(url):
    request = urllib.request.Request(url, headers={"User-Agent": "HexaLauncher-1.21.10-input-audit/1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def verify_download(label, item):
    url = item.get("url", "")
    expected = item.get("sha1", "")
    size = item.get("size")
    if not url.startswith("https://") or not re.fullmatch(r"[0-9a-f]{40}", expected):
        raise ValueError(f"{label}: invalid official URL or SHA-1 metadata")
    if not isinstance(size, int) or size <= 0:
        raise ValueError(f"{label}: invalid official file size")
    digest = hashlib.sha1()
    received = 0
    request = urllib.request.Request(url, headers={"User-Agent": "HexaLauncher-1.21.10-input-audit/1"})
    with urllib.request.urlopen(request, timeout=120) as response:
        while True:
            block = response.read(1024 * 1024)
            if not block:
                break
            received += len(block)
            digest.update(block)
    actual = digest.hexdigest()
    if received != size or actual != expected:
        raise ValueError(f"{label}: size/SHA-1 mismatch (bytes={received}, sha1={actual})")
    return {"bytes": received, "sha1": actual}


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
    for name in ("client_mappings", "server_mappings"):
        verified[name] = verify_download(name, downloads[name])

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
