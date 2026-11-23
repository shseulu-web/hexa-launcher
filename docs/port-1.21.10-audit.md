# Minecraft Java 1.21.10 port audit

Date: 2026-11-23
Target: Hexa Launcher, Android ARM64, Minecraft: Java Edition 1.21.10.

## Verified source facts

The current game implementation is pinned to Minecraft 26.3:

- `research-lock.json` pins `minecraft.version = 26.3`.
- `crates/horizon-core/src/version.rs` declares version 26.3, protocol 777, DataVersion 5023, resource pack 97.1, data pack 121.0 and Java 25.
- The Rust workspace contains the full Horizon/Starling game implementation, Android NativeActivity integration and the APK packaging workflow.

Some 1.21.10 multiplayer compatibility work already exists:

- `crates/horizon-protocol/src/adapter/v1_21_10.rs` maps protocol 773 packet IDs to/from the pinned protocol.
- `crates/horizon-protocol/src/adapter/v1_21_10_ids.rs` maps 1.21.10 block-state and registry IDs to/from the pinned version.
- `crates/horizon-protocol/src/adapter/client_session/step_1_21_10.rs` handles entity metadata layout differences.
- These files are generated/translation adapters. They do **not** make the local game client itself Minecraft 1.21.10.

## Why a version-string change is not a port

Changing only `VANILLA_VERSION`, protocol constants, or the launcher label would produce a mislabeled 26.3 client. The current version-port pipeline explicitly assumes unobfuscated Minecraft releases (26.1 and later); 1.21.10 predates that pipeline's supported decompilation path.

## Required engineering work

1. Obtain and verify the official 1.21.10 client/server artifacts and their metadata for development use.
2. Establish a reproducible decompilation and vanilla-oracle workflow for the obfuscated 1.21.10 jars, with pinned mapping/tool versions.
3. Generate 1.21.10 facts, packet IDs, registries, block states, item/component data, command tables, assets and data-pack reports.
4. Compare the 1.21.10 vanilla classes/methods with the 26.3 Rust port; classify every mismatch.
5. Port or remove 26.3-only gameplay, rendering, UI, entity, item, world-generation and data-fixer behavior.
6. Validate save compatibility, resource/data pack formats, login/configuration/play packet behavior, and real 1.21.10 server connections.
7. Run parity/regression tests and build/install the ARM64 APK on a real Android device before claiming support.

## Acceptance criteria

Hexa Launcher may be called a Minecraft 1.21.10 client only when the game implementation—not merely its protocol adapter—uses verified 1.21.10 game data and passes the version-specific tests above. Until then, report the exact supported baseline honestly.
