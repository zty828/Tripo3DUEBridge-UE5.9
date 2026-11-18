# Changelog

All notable changes to this project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/); this project follows
the upstream plugin version with a `-ue5.9` adaptation suffix.

## [1.0.5-ue5.9] - 2026-11-18

### Added
- **Unreal Engine 5.9 (Preview) support** by rebuilding the pure-source variant against
  UE 5.9 (BuildId 60351404). No C++ source changes were needed — the plugin's
  `TripoVersionCompat.h` already gates the 5.8+ Interchange API behind
  `UE_VERSION_AT_LEAST(5, 8)`, which 5.9 satisfies.
- Precompiled Win64 editor binary (`Binaries/Win64/UnrealEditor-Tripo3DUEBridge.dll`)
  for drop-in use without a compiler.
- End-to-end validator `tools/validate_bridge.py` (pure standard library) with a
  non-destructive `--ping-only` mode and a full FBX import round-trip mode.
- Repository structure checker `tools/check_repo.py` and a lightweight `validate` CI
  workflow (no Unreal Engine build on the runner).
- Documentation: bilingual README, `docs/ADAPTATION.md`, `VALIDATION.md`,
  `CONTRIBUTING.md`, `NOTICE.md`, issue/PR templates.

### Fixed
- Declared the missing **Interchange** plugin dependency in `Tripo3DUEBridge.uplugin`
  (the module depends on `InterchangeEngine` / `InterchangePipelines`; the upstream
  package omitted the declaration, which produced a UBT warning).

### Notes
- This is an **unofficial** community adaptation. Original plugin Copyright Tripo3D,
  All Rights Reserved; IXWebSocket Copyright machinezone (MIT). The repository's MIT
  license covers only the adaptation contributions. See [NOTICE.md](NOTICE.md).

[1.0.5-ue5.9]: https://github.com/zty828/Tripo3DUEBridge-UE5.9/releases/tag/v1.0.5-ue5.9
