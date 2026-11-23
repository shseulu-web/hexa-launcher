# Hexa Launcher — development status

## Product target

- Android app: Hexa Launcher
- Application ID: `com.hexablockyt.hexalauncher`
- Primary ABI: `arm64-v8a`
- Requested game: Minecraft: Java Edition 1.21.10
- Native implementation language: Rust
- Home screen: one primary button, `Launch 1.21.10 (Rust)`

## Implemented launcher-shell work

- Added `HexaHomeActivity` and routed the launcher entry point to it.
- Home screen has one main launch button and an original hexagonal H mark.
- Android APK packaging now generates custom Hexa app icons at the configured mipmap sizes.
- The launch action is deliberately blocked while the native engine is not a verified 1.21.10 build. It must not start the 26.3 engine under a 1.21.10 label.
- The custom Android home screen and icon generator have been committed, but the latest Android APK build must pass before distributing this shell.

## Actual engine baseline — not yet the requested version

The Rust game implementation remains pinned to Minecraft 26.3:

- Protocol 777
- DataVersion 5023
- Resource pack format 97.1
- Data pack format 121.0
- Java 25

The existing 1.21.10 protocol adapters cover network packet/ID and selected metadata translation only. They do not port local rendering, registries, blocks, items, entities, world generation, data fixing, saves or gameplay. The current application is therefore **not a Minecraft 1.21.10 client yet**.

## 1.21.10 reverse-engineering pipeline progress

- Official Mojang 1.21.10 metadata and mapping checksum audit: CI passed.
- Added `tools/proguard_to_tiny.py`, a local converter for official ProGuard mapping text to Tiny v2.
- Added synthetic unit tests and a CI workflow for the converter.
- Added `python tools/lab.py mappings --version 1.21.10` to download the official client/server mapping files into `.local/minecraft/1.21.10/mappings`, verify SHA-1, convert them locally and write a report.
- Mapping text and generated Tiny files are local development inputs and must not be committed or redistributed.
- This command prepares mappings only. It does not yet remap the game jars.
- `tools/lab.py prepare` still rejects mapping-bearing releases until the remap stage is implemented and tested.

## Remaining engineering work

1. Implement and test a pinned ProGuard/Tiny mapping application stage for both client and server jars.
2. Import the player's own legally obtained 1.21.10 game files locally and remap them reproducibly.
3. Decompile the remapped jars and validate source/class coverage against the official mapping inputs.
4. Generate 1.21.10 registries, block states, item/component data, commands, assets and data-pack reports.
5. Compare 1.21.10 vanilla behavior with the current Rust engine and port the missing/different implementation.
6. Port and validate rendering, gameplay, entities, world generation, saving/loading and data fixing.
7. Test 1.21.10 login/configuration/play protocol and real 1.21.10 server compatibility.
8. Build ARM64 APKs and test on a real Android device with the player's own game files.

## Release rule

Do not call the APK a Minecraft 1.21.10 client until the local game implementation uses verified 1.21.10 data and passes version-specific parity, world and server tests. Do not distribute Minecraft game assets or jars in the APK.
