# Hexa Launcher — development status

Hexa Launcher is being developed from the Starling Android application and Horizon's Rust game engine.

## Current base and build

- Android application label: Hexa Launcher
- Android application ID: `com.hexablockyt.hexalauncher`
- Development version: `0.1.0`
- Primary build target: Android ARM64 (`arm64-v8a`)
- Game implementation baseline: Minecraft: Java Edition 26.3 (Rust-native Horizon port).

## Minecraft 1.21.10 target

The requested target is Minecraft: Java Edition 1.21.10. The current game implementation is **not yet a verified 1.21.10 client**.

Existing compatibility work is present:
- Protocol 773 packet-ID translation for 1.21.10.
- 1.21.10 block-state and registry-ID translation.
- 1.21.10 entity-metadata layout translation.

These adapters allow protocol translation against the 26.3-pinned engine; they do not replace the engine's game version. The engine still declares 26.3 (protocol 777, DataVersion 5023, resource pack 97.1, data pack 121.0, Java 25). Do not relabel this build as 1.21.10.

A port audit and required work list is tracked in [docs/port-1.21.10-audit.md](docs/port-1.21.10-audit.md). The current automated version-port pipeline only handles unobfuscated releases from 26.1 onward, so 1.21.10 needs a reproducible legacy decompilation/oracle path before the full parity port can proceed.

## Build APK

The Android workflow builds APK artifacts for supported ABIs. Open the repository's **Actions → android** workflow and run it on branch `hexa-launcher-dev`. Download `hexa-launcher-apk-arm64-v8a` for most modern Android phones. The APK contains no Minecraft game files; the player must prepare game data from their own legally obtained copy.

## Next engineering tasks

1. Establish and pin the 1.21.10 decompilation/oracle toolchain.
2. Generate version-specific reports and data tables from official 1.21.10 artifacts.
3. Port all engine behavior that differs from 1.21.10 and add parity/regression tests.
4. Build and install the ARM64 APK, then validate it against 1.21.10 assets, worlds and servers.
5. Produce a signed release APK only after compatibility and device testing.
