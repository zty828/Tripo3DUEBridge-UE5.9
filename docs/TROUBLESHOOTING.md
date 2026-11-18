# Troubleshooting / 故障排查

Common problems and fixes for the **unofficial UE 5.9 adaptation** of the Tripo3D UE Bridge.
For verification procedures see [VALIDATION.md](../VALIDATION.md); for the technical
background of the port see [ADAPTATION.md](ADAPTATION.md).

> 中文提示：每节末尾附一句中文要点。排查前先确认三件事：UE 5.9 编辑器已打开、插件已启用、**Window → Tripo Bridge** 窗口已打开（窗口打开时才会启动 WebSocket 服务）。

## Quick checklist

Before digging into a specific symptom:

1. UE **5.9** editor is open and the plugin is enabled (**Edit → Plugins → Tripo3D → Tripo Bridge**).
2. **Window → Tripo Bridge** is open — the server auto-starts with the window and **stops when the window closes** (or when you press **Stop Server**).
3. Run the safe connectivity check: `python tools/validate_bridge.py --ping-only` (creates no assets).

## 1. Connection refused / validator can't connect

**Symptoms:** `Connection refused`, the validator exits with code 1 before the handshake, or Tripo Studio reports it cannot reach the bridge.

| Cause | Fix |
| --- | --- |
| Bridge window not open | The WebSocket server only runs while the Tripo Bridge window is open. Open **Window → Tripo Bridge**; the log should show `Server started automatically`. If you pressed **Stop Server**, press **Start Server** again. |
| Wrong host/port | The bridge is fixed at `ws://127.0.0.1:60620` (`TripoProtocol.h`). Point the client there. The validator defaults already match; `--host`/`--port` are only for pointing at something else (e.g. the mock bridge). |
| Port already in use | If the window log shows `Failed to start server`, another process may hold port 60620. Check with `netstat -ano \| findstr 60620` and close the conflicting process. |
| Firewall / security software | Loopback traffic is normally allowed, but endpoint protection can block local WebSocket connections. Allow `UnrealEditor.exe` through the firewall, or temporarily disable the security software to test. |

> 中文：服务只在桥接窗口打开时运行；先开窗口，再跑 `--ping-only`。端口固定 60620，启动失败先查端口占用。

## 2. Plugin won't load / engine version mismatch

**Symptoms:** the editor reports modules "missing or built with a different engine version", the Tripo Bridge menu entry is absent, or the validator fails its engine-version assertion.

- The bundled `Binaries/Win64/UnrealEditor-Tripo3DUEBridge.dll` is built **only** for UE 5.9 Preview, BuildId **60351404**. A different engine — or a different 5.9 build/hotfix with another BuildId — rejects it. Rebuild from source for your engine ([README → Install, Option B](../README.md#option-b--build-from-source)); the source path supports UE 5.4–5.8 through the plugin's version gates.
- The validator requires the reported engine version to contain `5.9` by default. When testing another engine, pass `--expect-engine 5.8` (or `--expect-engine ""` to skip the check).
- After enabling the plugin or replacing binaries, **restart the editor**.

> 中文：预编译 DLL 只认 UE 5.9 BuildId 60351404；其他版本（含不同 hotfix）请从源码重编。

## 3. Import fails or no assets appear

**Symptoms:** the transfer finishes but nothing shows up in the Content Browser, or `import_complete` reports `success=false`.

1. **Interchange enabled?** The plugin imports through UE's Interchange pipeline. The `.uplugin` declares the dependency, but a project-level disable overrides it: check **Edit → Plugins → Interchange**, enable it, and restart the editor.
2. **Read the logs.** The bridge window's transfer log shows per-chunk acks → `file_transfer_complete` (`importing`) → `import_complete`. In **Window → Output Log**, filter for `Tripo` — the importer logs `[Tripo]` / `[Tripo][PBR]` messages along with any Interchange errors.
3. **Look in the right place.** Assets land under `/Game/TripoModels/<model-name>/`, with textures in a `Textures/` subfolder.
4. **Reproduce deterministically:** `python tools/validate_bridge.py --fbx path/to/model.fbx` (creates assets). Exit codes: `0` pass · `2` the editor reported a failed import (read its `message`) · `1` connection/timeout/engine mismatch. For heavy models raise `--import-timeout` (default 300 s).

> 中文：确认 Interchange 插件已启用；Output Log 过滤 `Tripo`；资产在 `/Game/TripoModels` 下；用 `--fbx` 做全流程复现。

## 4. Textures or materials missing

**Symptoms:** the mesh imports but appears untextured, grey, or with default materials.

- **`.fbm` sidecar folder (embedded textures).** An FBX with embedded media is extracted together with a `<name>.fbm` folder next to it. When importing such an FBX manually, keep the FBX and its `.fbm` folder together — moving or deleting the folder loses the textures. For bridge pushes, the plugin stages files under `<Project>/Intermediate/Tripo3D/<fileId>/` and cleans that folder up after import; don't delete it mid-import.
- **Textures in the payload.** Bridge transfers carry the textures alongside the FBX (ZIP payloads are extracted automatically). The log line `[Tripo][PBR] Imported N additional PBR texture(s)` tells you how many were found — `N=0` usually means the push contained no textures; re-push from Tripo Studio with textures included.
- **Complete plugin copy.** PBR materials are built from the plugin's own `Content/` assets (master material `M_Tripo_PBR_Master` + default textures). If `Content/` was not copied into `Plugins/Tripo3DUEBridge/`, material creation fails — copy the whole folder again.
- Imported textures live under `/Game/TripoModels/<model-name>/Textures/`; check they exist before re-pushing.

> 中文：手动导入时保留 `.fbm` 伴随文件夹；桥接推送请确认带贴图、`Content/` 完整拷入；看 `[Tripo][PBR]` 日志。

## 5. Building from source: Live Coding lock

**Symptom:** UBT refuses with `Unable to build while Live Coding is active`.

An open editor holds an **engine-wide** Live Coding lock. **Close every running Unreal editor** (not just this project), then:

1. Right-click the `.uproject` → **Generate Visual Studio project files**.
2. Build the **Editor** target (VS2022, MSVC v14.44+, Windows SDK 10.0.22621).

> 中文：编译前关闭所有正在运行的 UE 编辑器，再重新生成工程文件并编译 Editor 目标。

## 6. BuildId / `.modules` mismatch

**Symptoms:** "The following modules are missing or built with a different engine version: Tripo3DUEBridge", or a rebuild prompt on every launch.

`Binaries/Win64/UnrealEditor.modules` records the BuildId the DLL was compiled against; the editor only loads modules whose BuildId matches the running engine. Fix:

1. Delete the plugin's `Binaries/` and `Intermediate/` folders.
2. Rebuild from source against **your** engine ([README → Option B](../README.md#option-b--build-from-source)). Don't hand-edit `.modules`.

Why the official 5.8 binary can't be reused: [ADAPTATION.md §1](ADAPTATION.md).

> 中文：删除插件的 `Binaries/` 与 `Intermediate/`，按你的引擎从源码重编；不要手改 `.modules`。

## 7. Running the validation tools

All tools are Python 3.8+, **standard library only** — nothing to install.

### `tools/validate_bridge.py` — against a live editor

Requires: editor open, plugin enabled, Tripo Bridge window open.

```bash
# Safe: handshake + ping/pong only, creates NO assets
python tools/validate_bridge.py --ping-only

# Full round-trip: pushes a real FBX, CREATES assets under /Game/TripoModels
python tools/validate_bridge.py --fbx path/to/model.fbx
```

Useful flags: `--host` / `--port` (default `127.0.0.1:60620`), `--expect-engine` (default `5.9`, `""` disables), `--timeout` (per-message, 30 s), `--import-timeout` (300 s). Exit codes: `0` pass · `2` import reported failure · `1` connection/timeout/engine mismatch. Full walkthrough: [VALIDATION.md](../VALIDATION.md).

### `tools/selftest.py` — no editor needed

```bash
python tools/selftest.py
```

Runs the validator end-to-end against a faithful in-process mock bridge (`tools/mock_bridge.py`, port 60621): ping-only, single-chunk and multi-chunk (>5 MiB) transfers with SHA-256 integrity assertions, plus a negative engine-version case. Exit `0` = all pass; prints a `SELFTEST={...}` JSON summary. Needs `tools/mock_bridge.py` alongside it; safe to run in CI. It exercises the **validator and protocol**, not the editor's importer.

### `tools/check_repo.py` — no editor needed

```bash
python tools/check_repo.py
```

Verifies the drop-in layout, the `.uplugin` manifest (including the Interchange dependency), license/provenance files and the precompiled binary — the same check CI runs on every push/PR.

> 中文：`--ping-only` 只做握手+心跳，不产生资产，安全；`--fbx` 全流程会创建资产。`selftest.py` 无需编辑器，离线自检校验器与协议。

## Still stuck?

Collect and attach:

- Engine version + BuildId (**Help → About Unreal Editor**, or the engine's `Build.version`).
- The bridge window's transfer log and the relevant **Output Log** lines (filter `Tripo`).
- The validator's `RESULT_JSON=...` line (or `SELFTEST=...` for the offline self-test).

Then [open an issue](https://github.com/zty828/Tripo3DUEBridge-UE5.9/issues/new/choose) — the bug template lists what to include.

Remember this is an **unofficial** adaptation: problems in the original plugin's behavior may belong upstream with [Tripo3D](https://www.tripo3d.ai); this repo covers the UE 5.9 build/port. Provenance and licensing: [NOTICE.md](../NOTICE.md).
