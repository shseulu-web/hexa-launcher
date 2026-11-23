#!/usr/bin/env python3
"""Prepare and decompile Minecraft Java 1.21.10 locally.

The client jar must come from the user's official Minecraft launcher installation.
The official server jar, libraries, mappings and tools are cached under .local/ and
must never be committed or redistributed.
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import lab  # noqa: E402

VERSION = "1.21.10"
META_MANIFEST = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
REMAPPER_VERSION = "0.14.1"
REMAPPER_BASE = f"https://maven.fabricmc.net/net/fabricmc/tiny-remapper/{REMAPPER_VERSION}/tiny-remapper-{REMAPPER_VERSION}-fat.jar"


def fetch_json(url):
    request = urllib.request.Request(url, headers={"User-Agent": "HexaLauncher-1.21.10-prep/1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def release_metadata():
    manifest = fetch_json(META_MANIFEST)
    entry = next((item for item in manifest["versions"]
                  if item.get("id") == VERSION and item.get("type") == "release"), None)
    if not entry:
        raise ValueError(f"Mojang release manifest does not contain {VERSION}")
    data = fetch_json(entry["url"])
    if data.get("id") != VERSION:
        raise ValueError(f"Expected {VERSION} metadata, got {data.get('id')!r}")
    if data.get("javaVersion", {}).get("majorVersion") != 21:
        raise ValueError("Minecraft 1.21.10 metadata does not specify Java 21")
    for side in ("client", "server"):
        if not data.get("downloads", {}).get(side, {}).get("sha1"):
            raise ValueError(f"Mojang metadata has no {side} download checksum")
    return data


def verified_copy_or_download(source, destination, sha1, url=None):
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file() and lab.digest(destination, "sha1") == sha1:
        return destination
    if source is not None:
        if not source.is_file():
            raise FileNotFoundError(f"Missing official launcher file: {source}")
        if lab.digest(source, "sha1") != sha1:
            raise ValueError(f"Launcher file checksum mismatch: {source}")
        shutil.copyfile(source, destination)
    elif url:
        lab.download(url, destination, sha1, "sha1")
    else:
        raise ValueError("No source file or official download URL supplied")
    return destination


def fetch_remapper():
    tools_dir = lab.LOCAL / "tools"
    jar = tools_dir / f"tiny-remapper-{REMAPPER_VERSION}-fat.jar"
    checksum_url = REMAPPER_BASE + ".sha256"
    with urllib.request.urlopen(checksum_url, timeout=30) as response:
        checksum_text = response.read().decode("ascii").strip()
    checksum = checksum_text.split()[0].lower()
    if not re.fullmatch(r"[0-9a-f]{64}", checksum):
        raise ValueError("Fabric Maven returned an invalid TinyRemapper SHA-256 file")
    lab.download(REMAPPER_BASE, jar, checksum, "sha256")
    return jar, checksum


def prepare(minecraft_dir):
    metadata = release_metadata()
    directory = lab.LOCAL / "minecraft" / VERSION
    jars_dir = directory / "jars"
    game_dir = Path(minecraft_dir).expanduser()
    client_source = game_dir / "versions" / VERSION / f"{VERSION}.jar"
    client = verified_copy_or_download(
        client_source, jars_dir / "client.jar", metadata["downloads"]["client"]["sha1"]
    )
    server = verified_copy_or_download(
        None, jars_dir / "server-bundle.jar", metadata["downloads"]["server"]["sha1"],
        metadata["downloads"]["server"]["url"]
    )

    client_libraries = []
    for artifact in lab.client_library_artifacts(metadata):
        relative = Path(artifact["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"Unsafe library path: {artifact['path']}")
        local = directory / "libraries" / "client" / relative
        source = game_dir / "libraries" / relative
        url = artifact.get("url")
        if not url:
            url = "https://libraries.minecraft.net/" + artifact["path"]
        verified_copy_or_download(source if source.is_file() else None, local, artifact["sha1"], url)
        client_libraries.append(local)

    server_game, server_libraries = lab.unpack_server(server, directory, VERSION)
    mappings_report = lab.official_mappings(VERSION)
    mapping_dir = directory / "mappings"
    if not (mapping_dir / "client.tiny").is_file() or not (mapping_dir / "server.tiny").is_file():
        raise ValueError("Official mappings were not generated successfully")

    remapper, remapper_sha256 = fetch_remapper()
    java = shutil.which("java")
    if not java:
        raise FileNotFoundError("Java 21 is required; Java was not found on PATH")
    java_version = subprocess.run([java, "-version"], capture_output=True, text=True, check=True)
    match = re.search(r'version "([0-9]+)', java_version.stderr + java_version.stdout)
    if not match or int(match.group(1)) < 21:
        raise ValueError("Java 21 or newer is required for the 1.21.10 preparation pipeline")

    outputs = {}
    for side, source, classpath in (
        ("client", client, client_libraries),
        ("server", server_game, server_libraries),
    ):
        named = jars_dir / f"{side}-named.jar"
        if named.exists():
            raise FileExistsError(f"Refusing to overwrite {named}; move the old output first")
        outputs[side] = lab.remap_jar(
            java, remapper, source, mapping_dir / f"{side}.tiny", named, side, classpath
        )
        inventory = lab.inventory(named)
        lab.write_json(directory / "reports" / f"{side}-inventory.json", inventory)

    vineflower = lab.config()[0]["vineflower"]
    vf_jar = lab.LOCAL / "tools" / f"vineflower-{vineflower['version']}.jar"
    lab.download(vineflower["url"], vf_jar, vineflower["sha256"], "sha256")
    prepared = {
        "version": VERSION,
        "java_major": 21,
        "mappings": mappings_report,
        "tiny_remapper": {"version": REMAPPER_VERSION, "sha256": remapper_sha256},
        "vineflower": {"version": vineflower["version"], "sha256": vineflower["sha256"]},
        "jars": {side: str(path.relative_to(ROOT)) for side, path in outputs.items()},
        "libraries": {
            "client": [str(path.relative_to(ROOT)) for path in client_libraries],
            "server": [str(path.relative_to(ROOT)) for path in server_libraries],
        },
    }
    lab.write_json(directory / "prepared-1.21.10.json", prepared)
    print(json.dumps(prepared, indent=2))
    print("Remapping complete. Run the decompile command next; this is not yet a Rust engine port.")


def decompile(side, java_name, threads, heap):
    directory = lab.LOCAL / "minecraft" / VERSION
    prepared_path = directory / "prepared-1.21.10.json"
    if not prepared_path.is_file():
        raise FileNotFoundError("Run prepare first; prepared-1.21.10.json is missing")
    prepared = json.loads(prepared_path.read_text(encoding="utf-8"))
    vf = lab.config()[0]["vineflower"]
    tool = lab.LOCAL / "tools" / f"vineflower-{vf['version']}.jar"
    if lab.digest(tool, "sha256") != vf["sha256"]:
        raise ValueError("Vineflower checksum mismatch; rerun prepare")
    java = shutil.which(java_name)
    if not java:
        raise FileNotFoundError("Java 21 is required; Java was not found on PATH")
    version = subprocess.run([java, "-version"], capture_output=True, text=True, check=True)
    match = re.search(r'version "([0-9]+)', version.stderr + version.stdout)
    if not match or int(match.group(1)) < 21:
        raise ValueError("Java 21 or newer is required")
    sides = ("client", "server") if side == "both" else (side,)
    incomplete = False
    for current in sides:
        jar = ROOT / prepared["jars"][current]
        inventory_path = directory / "reports" / f"{current}-inventory.json"
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
        if lab.digest(jar, "sha256") != inventory["jar_sha256"]:
            raise ValueError(f"{current} remapped jar changed; rerun prepare")
        destination = directory / "sources" / current
        if destination.exists():
            raise FileExistsError(f"Refusing to overwrite existing source directory: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        stage = destination.with_name(destination.name + ".incomplete")
        if stage.exists():
            shutil.rmtree(stage)
        stage.mkdir()
        command = [java, f"-Xmx{heap}", "-jar", str(tool), "--folder", "--skip-extra-files=1",
                   "--log-level=warn", f"--thread-count={threads}"]
        command += [f"--add-external={ROOT / item}" for item in prepared["libraries"][current]]
        command += [str(jar), str(stage)]
        log = directory / "reports" / f"{current}-decompiler.log"
        with log.open("w", encoding="utf-8") as stream:
            result = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT)
        if result.returncode:
            raise RuntimeError(f"{current} decompilation failed; inspect {log}; partial output: {stage}")
        stage.rename(destination)
        report = lab.coverage(directory, current, destination)
        report["java_version"] = (version.stderr + version.stdout).strip()
        report["vineflower_version"] = vf["version"]
        lab.write_json(directory / "reports" / f"{current}-coverage.json", report)
        incomplete |= bool(report["missing_source_files"] or report["files_with_decompiler_error_markers"])
        print(json.dumps(report, indent=2))
    if incomplete:
        raise RuntimeError("Decompilation completed with missing source files or decompiler error markers")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare", help="Remap official 1.21.10 client and server jars")
    prep.add_argument("--minecraft-dir", type=Path, required=True,
                      help="Official Minecraft launcher game directory containing versions/1.21.10/1.21.10.jar")
    dec = commands.add_parser("decompile", help="Decompile remapped jars and verify source-file coverage")
    dec.add_argument("--side", choices=("client", "server", "both"), default="both")
    dec.add_argument("--java", default="java")
    dec.add_argument("--threads", type=int, default=4)
    dec.add_argument("--heap", default="6G")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.minecraft_dir)
    else:
        if args.threads < 1 or not re.fullmatch(r"[1-9][0-9]*[MGmg]", args.heap):
            parser.error("--threads must be positive and --heap must look like 6G or 512M")
        decompile(args.side, args.java, args.threads, args.heap)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError, zipfile.BadZipFile,
            RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(1)
