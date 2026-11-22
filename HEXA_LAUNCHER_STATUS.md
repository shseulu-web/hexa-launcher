# Hexa Launcher — development status

Hexa Launcher is being developed from the Starling Android application and Horizon's Rust game engine.

## Current base and build

- Android application label: Hexa Launcher
- Android application ID: `com.hexablockyt.hexalauncher`
- Development version: `0.1.0`
- Primary build target: Android ARM64 (`arm64-v8a`)
- The existing upstream game implementation in this source tree targets Minecraft: Java Edition 26.3.

## Compatibility target

The requested target is Minecraft: Java Edition 1.21.10. This is **not yet implemented or verified** in this codebase. The current 26.3 engine must be audited and adapted for 1.21.10 protocol, data version, registries, assets, resource preparation, world formats and server compatibility. Do not label a 26.3 build as 1.21.10.

## Build APK

The Android workflow builds APK artifacts for the supported ABIs. Open the repository's **Actions → android** workflow and run it on branch `hexa-launcher-dev`. Download `hexa-launcher-apk-arm64-v8a` for most modern Android phones. The APK contains no Minecraft game files; the player must prepare game data from their own legally obtained copy.

## Next engineering tasks

1. Confirm the current Android build and install it on an ARM64 device.
2. Audit the Horizon 26.3 implementation against Minecraft 1.21.10.
3. Implement and test compatibility changes incrementally, with protocol and world-format regression tests.
4. Replace remaining Starling-facing names, icons, strings and documentation with Hexa Launcher branding.
5. Produce a signed release APK only after compatibility and device testing.
