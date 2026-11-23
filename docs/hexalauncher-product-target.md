# Hexa Launcher product target

This document records the requested product target. It is not a claim that the target is implemented.

## Product identity

- Android application: Hexa Launcher
- Primary ABI: Android ARM64 (arm64-v8a)
- Game implementation language: Rust
- Exact target: Minecraft: Java Edition 1.21.10
- Launcher start screen: one primary action labelled **Launch 1.21.10 (Rust)**
- No additional launcher navigation buttons on the initial screen.
- Use the Hexa voxel emblem as the app icon and launcher identity.

## Non-negotiable version correctness

The launcher must not display or claim 1.21.10 while executing the existing 26.3 engine. Updating a label, protocol adapter, or compatibility translation is not a game-version port.

The implementation must use verified 1.21.10 values for:
- game version identity and runtime version reporting
- protocol version and packet definitions
- DataVersion and data-fixer behavior
- client resource-pack and server data-pack formats
- Java runtime requirement
- registries, block states, items/components, entities, commands, world generation, rendering and gameplay data

## Launch behavior

The single launch action must:
1. Verify that the required game data has been prepared from the player's own legitimate Minecraft installation.
2. Refuse to launch if required 1.21.10 data is missing or inconsistent.
3. Start the Rust-native 1.21.10 engine.
4. Report actionable errors without silently falling back to 26.3.

## Acceptance criteria

- A real 1.21.10 world can be opened and saved.
- A real 1.21.10 server can complete login, configuration and play.
- Version-specific rendering, registries, gameplay and data-fixer parity tests pass.
- Runtime diagnostics report 1.21.10, never 26.3.
- The app opens to the single-action launcher screen.
- The ARM64 APK installs and runs on a physical Android device.

## Current state

The repository baseline is Horizon 26.3. Existing 1.21.10 protocol adapters are only compatibility translations and do not constitute a local 1.21.10 game implementation. The full port remains incomplete. The current APK must therefore not be represented as a 1.21.10 build.
