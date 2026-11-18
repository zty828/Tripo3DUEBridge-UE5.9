# Contributing

Thanks for helping improve the UE 5.9 adaptation of the Tripo3D UE Bridge!

## Ground rules

- **This is an unofficial adaptation.** The original plugin is Copyright Tripo3D,
  All Rights Reserved. Keep the upstream copyright headers in every source file intact.
  Do not relicense upstream code. New adaptation-layer contributions are accepted under
  the MIT terms that cover this repository's own additions (see [LICENSE](LICENSE) and
  [NOTICE.md](NOTICE.md)).
- **Do not commit build intermediates or debug symbols.** `Intermediate/`, `Saved/`,
  `*.pdb`, `*.exp` are git-ignored. The precompiled `Binaries/Win64/*.dll`,
  `*.modules`, `*.uclasses` *are* committed on purpose (drop-in binary).
- **Target UE 5.9 (Win64).** The bundled `IXWebSocket.lib` and editor binary are Win64.

## Building from source

1. Install Unreal Engine 5.9 and Visual Studio 2022 (MSVC v143, Windows 10/11 SDK).
2. Copy this folder into `<YourProject>/Plugins/Tripo3DUEBridge`.
3. Enable the plugin in the `.uproject` (it is editor-only).
4. Generate project files and build the editor target. The module links the bundled
   `ThirdParty/IXWebSocket/Lib/Win64/IXWebSocket.lib` and the engine's zlib (1.3 on 5.7+).
5. If you change C++, rebuild and refresh the committed `Binaries/Win64` binary so the
   drop-in download stays in sync.

> Close any running UE editor before building — Live Coding holds a global lock that
> blocks UBT (`Unable to build while Live Coding is active`).

## Before opening a pull request

- Run the structure check: `python tools/check_repo.py` (must print `RESULT: PASS`).
- If you touched the bridge protocol or importer, run the live validator against a 5.9
  editor (see [VALIDATION.md](VALIDATION.md)):
  `python tools/validate_bridge.py --ping-only` and, for import changes,
  `python tools/validate_bridge.py --fbx <model.fbx>`.
- Update [CHANGELOG.md](CHANGELOG.md) and any affected docs.
- Keep the diff focused; preserve upstream copyright headers.

The `validate` CI workflow runs `tools/check_repo.py` and a syntax check of the validator
on every push/PR. It does **not** compile Unreal Engine (no engine on the runner) — full
build/import verification is done locally as described above.

## Reporting issues

Use the issue templates. Include your exact UE version (e.g. 5.9 Preview BuildId),
plugin commit, OS, and the relevant editor log lines (`LogTemp` / `Tripo3D Server`).
