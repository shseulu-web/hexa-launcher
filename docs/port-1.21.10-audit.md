# Minecraft Java 1.21.10 port audit

Date: 2026-11-23
Target: Hexa Launcher, Android ARM64, Minecraft: Java Edition 1.21.10.

## Verified source facts

The current Rust game implementation is pinned to Minecraft 26.3:

- `research-lock.json` pins `minecraft.version = 26.3`.
- `crates/horizon-core/src/version.rs` declares version 26.3, protocol 777, DataVersion 5023, resource pack 97.1, data pack 121.0 and Java 25.
- Existing 1.21.10 adapters translate protocol 773 packet IDs, selected block-state/registry IDs and entity metadata. They do not port the local game engine.

Minecraft Java 1.21.10 is protocol 773, DataVersion 4556, resource-pack format 69, data-pack format 88 and Java 21. Mojang's version metadata includes official client and server ProGuard mappings.

## Work committed so far

1. Official Mojang metadata and mapping SHA-1 verifier: `tools/verify_minecraft_1_21_10_inputs.py`.
2. CI workflow for official input verification.
3. Local ProGuard-to-Tiny-v2 converter: `tools/proguard_to_tiny.py`.
4. Synthetic tests for class, field, method, descriptor and array conversion.
5. CI workflow that syntax-checks the tooling and runs the converter tests.
6. `python tools/lab.py mappings --version 1.21.10` downloads official mapping text to `.local`, verifies the published SHA-1, converts client/server mappings to Tiny v2 and writes a local report.
7. Added a local TinyRemapper execution stage to `tools/lab.py prepare`: it accepts a developer-supplied TinyRemapper fat JAR, remaps client/server jars from `official` to `named`, passes each side's dependency classpath, preserves originals, and validates output ZIP integrity before promoting it.
8. Added a mocked unit test for the remapping command construction, namespace selection, archive validation and overwrite protection.

Mapping data and generated mappings remain local and are not committed.

## Important limitation

The remapper stage is wired into `prepare`, but the real 1.21.10 client/server remap has **not** yet been run or validated against Mojang's actual jars. TinyRemapper is supplied locally by the developer and is not yet version-pinned in the repository. The mocked test checks orchestration only; it does not prove that a real remapper invocation succeeds or that the resulting classes are semantically correct.

## Required remaining work

1. Pin and checksum a TinyRemapper release; run it on the actual 1.21.10 client/server jars and validate remapped class names, descriptors, members and archive integrity.
2. Import the player's own 1.21.10 client/server jars locally; do not commit or redistribute game binaries.
3. Feed remapped jars to the pinned Vineflower pipeline and validate decompilation coverage.
4. Generate 1.21.10 protocol, registry, block-state, item/component, command, asset and data-pack facts.
5. Compare the decompiled 1.21.10 vanilla behavior with the current 26.3 Rust implementation.
6. Port the local game implementation: registries, rendering, blocks, items, entities, gameplay, world generation, data fixing, saving/loading and UI.
7. Test resource/data-pack formats, worlds, login/configuration/play packets and real 1.21.10 server connections.
8. Build and install ARM64 APKs and test on physical Android hardware.

## Acceptance criteria

Hexa Launcher may be described as a Minecraft 1.21.10 client only when its **local Rust game implementation**, not just its protocol adapter or launcher label, uses verified 1.21.10 data and passes version-specific game, world and server tests.
