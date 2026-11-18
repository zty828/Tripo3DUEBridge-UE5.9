# Validation

How to verify the Tripo3D UE Bridge actually works on **Unreal Engine 5.9**.

> 中文摘要：本仓库附带一个纯标准库的端到端验证器 `tools/validate_bridge.py`。`--ping-only` 只做握手+心跳（不产生任何资产，安全）；默认模式会推送一个 FBX 并等待导入完成。运行前需先打开 UE 编辑器并启用本插件、打开 Window → Tripo Bridge 窗口（会自动启动 `ws://127.0.0.1:60620`）。

## What is already verified

| Check | Status | Evidence |
| --- | --- | --- |
| Compiles against UE 5.9 (BuildId 60351404) | ✅ | UBT build succeeded, editor module DLL linked |
| Module loads in a UE 5.9 editor | ✅ | Runtime log: `InternalLoadLibrary 'Tripo3DUEBridge'` + `Tripo Bridge module started successfully` |
| Interchange import API matches UE 5.9 headers | ✅ | `FrameAlignment` / `EInterchangeFrameAlignment::SnapToClosest` verified against 5.9 headers |
| Offline protocol self-test (multi-chunk + SHA-256 integrity) | ✅ | `tools/selftest.py` vs `tools/mock_bridge.py` — runs in CI, no editor needed |
| Live "push model → import" round-trip | ⏳ pending | Use the validator below when an editor is available |

The compile / module-load / API checks and the offline protocol self-test are hard-verified.
The live round-trip is exercised by the validator; it requires a running editor, so run it
yourself with the steps below.

## Prerequisites

1. Unreal Engine **5.9** with this plugin installed under `<Project>/Plugins/Tripo3DUEBridge` and enabled.
2. Open the project in the editor.
3. Open **Window → Tripo Bridge**. Opening the window auto-starts the WebSocket server at `ws://127.0.0.1:60620`.
4. Python 3.8+ (standard library only — nothing to install).

## Mode 1 — ping-only (non-destructive)

Confirms the bridge is alive and talking to a 5.9 editor. Creates **no assets**.

```bash
python tools/validate_bridge.py --ping-only
```

Expected output (abridged):

```text
[validate] connecting ws://127.0.0.1:60620 ...
[validate] WebSocket upgraded
[validate] handshake OK - editor reports engine: 5.9.0-...
[validate] ping/pong OK
[validate] PASS (ping-only): bridge alive on 5.9.0-...
RESULT_JSON={"success": true, "mode": "ping-only", "engineVersion": "5.9.0-..."}
```

The validator asserts the engine version reported by the editor (`dccVersion`) contains
`5.9` by default. Use `--expect-engine ""` to skip that assertion, or `--expect-engine 5.8`
to test a different engine.

## Mode 2 — full import round-trip

Pushes a real FBX through the chunked transfer protocol and waits for the engine import.
**Creates assets** under `/Game/TripoModels` in the open editor.

```bash
python tools/validate_bridge.py --fbx /path/to/model.fbx
```

Expected output (abridged):

```text
[validate] handshake OK - editor reports engine: 5.9.0-...
[validate] ping/pong OK
[validate] transferring model.fbx: 153228 bytes in 1 chunk(s)
[validate] chunk 1/1 acknowledged
[validate] transfer complete: importing
[validate] PASS: import_complete success - Import complete: model.fbx
RESULT_JSON={"success": true, "mode": "full", "engineVersion": "5.9.0-...", "message": "Import complete: model.fbx", "fileId": "validate-..."}
```

After a PASS, check the Content Browser under `/Game/TripoModels` for the imported mesh,
materials and textures.

## Options

| Flag | Default | Meaning |
| --- | --- | --- |
| `--host` | `127.0.0.1` | Bridge host |
| `--port` | `60620` | Bridge port |
| `--fbx` | — | FBX to import (required for full mode) |
| `--ping-only` | off | Handshake + ping only, no assets created |
| `--client-name` | `UE59-Validator` | Name sent in the handshake |
| `--expect-engine` | `5.9` | Substring required in the reported engine version (`""` disables) |
| `--timeout` | `30` | Per-message timeout (seconds) |
| `--import-timeout` | `300` | Max wait for `import_complete` (seconds) |

## Exit codes

- `0` — PASS
- `2` — the editor reported `import_complete` with `success=false`
- `1` — connection error / timeout / engine-version mismatch

## Protocol notes (for maintainers)

The validator mirrors the server implementation exactly:

- Client→server **binary** frame = JSON header + raw chunk bytes; the server splits them
  with a brace-counting scanner (`FTripoWebSocketServer::FindJsonEnd`).
- `handshake` → `handshake_ack` (payload carries `dccVersion`, the engine version).
- `ping` → `pong`.
- `file_transfer` (per chunk) → `file_transfer_ack`; when all chunks arrive →
  `file_transfer_complete` (`status: importing`) → `import_complete` (`success`, `message`).

Source of truth: `Source/Tripo3DUEBridge/Private/TripoWebSocketServer.cpp` and
`TripoFileTransferManager.cpp`.

## Repository structure check (no editor needed)

```bash
python tools/check_repo.py
```

Verifies the drop-in layout, the `.uplugin` manifest (including the Interchange dependency),
license/provenance files, the precompiled binary, and that no PDB/Intermediate artifacts were
committed. This is what the `validate` CI workflow runs on every push/PR.

## Offline protocol self-test (no editor, runs in CI)

```bash
python tools/selftest.py
```

Exercises `tools/validate_bridge.py` end-to-end against `tools/mock_bridge.py`, a faithful
standard-library mock of the bridge WebSocket protocol (same JSON control frames and
JSON-header + raw-chunk binary frames, brace-counting split). **No Unreal Engine required.**

It covers four cases and asserts end-to-end integrity:

| Case | What it proves | Expected exit |
| --- | --- | --- |
| `ping_only` | handshake + heartbeat, engine-version assertion (`5.9`) | `0` |
| `single_chunk` | one-chunk FBX transfer → `import_complete` | `0` |
| `multi_chunk` | a >5 MiB payload split into 3 chunks, reassembled byte-for-byte (SHA-256 matches the source) | `0` |
| `wrong_engine` | negative case: `--expect-engine 5.8` against a 5.9 mock must fail | `1` |

The mock writes one JSON line per completed import (`bytes`, `chunks`, `sha256`); the
self-test checks the reassembled SHA-256 equals the source payload for both the single- and
multi-chunk cases. A final `SELFTEST={... "pass": true}` line and exit `0` mean all cases
passed. The `validate` CI workflow runs this on every push/PR, so protocol regressions are
caught without an editor.
