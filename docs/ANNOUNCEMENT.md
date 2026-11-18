# Release Announcement — DRAFT

> **Status: DRAFT — not posted anywhere.** For review before any external posting.
> Suggested targets: Reddit r/unrealengine, Unreal Engine forums, Tripo community channels (Discord / forum).
> Each language version below is self-contained and post-ready: copy the title + body of ONE version.
> This header and the pre-posting checklist at the bottom are review notes, not part of the post.

---

## English version

**Suggested title:**

> [Unofficial] Tripo3D UE Bridge adapted for UE 5.9 Preview — drop-in Win64 binary, zero C++ changes

**Body:**

The official Tripo3D UE Bridge binaries cover UE 5.4–5.8, and they won't load in UE 5.9 (the module BuildId and the pinned EngineVersion no longer match). I rebuilt the plugin from its pure-source variant for **UE 5.9 Preview** and published a ready-to-use precompiled Win64 binary, so you can keep pushing Tripo Studio models into the editor without needing a compiler.

**What it is:** an *unofficial* community adaptation of the Tripo3D UE Bridge — same plugin, same protocol. Tripo Studio pushes AI-generated FBX models + PBR textures over a local WebSocket (`ws://127.0.0.1:60620`), and the editor imports them into `/Game/TripoModels` via Interchange, with materials and textures wired up automatically.

**The fun part: no C++ changes were needed.** The plugin's own `TripoVersionCompat.h` already gates the 5.8+ Interchange API behind `UE_VERSION_AT_LEAST(5, 8)`, which 5.9 satisfies. The only fix required was declaring the missing **Interchange** plugin dependency in the `.uplugin`.

What you get:

- Drop-in precompiled Win64 editor binary (UE 5.9 Preview, BuildId 60351404) — or build from source
- WebSocket import of FBX + PBR textures, automatic PBR material setup, optional scene spawning
- Editor window with live connection status, start/stop and a transfer log; UI localized in 9 languages
- A dependency-free bridge validator (`tools/validate_bridge.py`) plus lightweight CI on every push

**Verification status (the honest version):**

- ✅ Compiles clean against UE 5.9, and the module loads in the editor
- ✅ The runtime import path was checked against the UE 5.9 Interchange headers
- ✅ The bundled validator was self-tested end-to-end against a faithful protocol mock
- ⏳ The live "push from Tripo Studio → import" round-trip hasn't been exercised on this port yet. You can check it in seconds with the validator: `--ping-only` (safe, creates no assets) or a full FBX import test. Reports very welcome.

**Install:**

1. One-click download: [Tripo3DUEBridge-UE5.9-Win64.zip](https://github.com/zty828/Tripo3DUEBridge-UE5.9/releases/download/v1.0.5-ue5.9/Tripo3DUEBridge-UE5.9-Win64.zip) (~1.9 MB)
2. Extract into your project's `Plugins/` folder → `YourProject/Plugins/Tripo3DUEBridge/`
3. Enable **Tripo3D → Tripo Bridge** under Edit → Plugins, then restart the editor
4. Open **Window → Tripo Bridge** (the server auto-starts) and push a model from Tripo Studio

The DLL is tied to 5.9 Preview BuildId **60351404** — if your 5.9 build/hotfix differs, rebuild from source (steps in the README). Win64 only, editor-only: nothing ships into packaged games.

**Links:** [Repository](https://github.com/zty828/Tripo3DUEBridge-UE5.9) · [Release v1.0.5-ue5.9](https://github.com/zty828/Tripo3DUEBridge-UE5.9/releases/tag/v1.0.5-ue5.9)

**License / provenance:** this is unofficial and not affiliated with or endorsed by Tripo3D. MIT covers only the adaptation contributions; the original plugin code remains © Tripo3D (All Rights Reserved), and IXWebSocket is © machinezone (MIT). Commercial redistribution of the original code requires authorization from Tripo3D — full details in NOTICE.md.

If you try it on 5.9, please share how the live push goes — issues and PRs welcome.

---

## 中文版本

**建议标题：**

> 【非官方】Tripo3D UE Bridge 适配 UE 5.9 预览版——预编译 Win64 直接放入，C++ 零改动

**正文：**

Tripo3D 官方的 UE Bridge 预编译二进制覆盖 UE 5.4–5.8，但在 UE 5.9 里无法加载（模块 BuildId 与钉死的 EngineVersion 不匹配）。我用插件的纯源码变体在 **UE 5.9 预览版**上重新编译，并发布了一个开箱即用的 Win64 预编译二进制——不用装编译器，就能继续把 Tripo Studio 的模型推进编辑器。

**这是什么：** Tripo3D UE Bridge 的*非官方*社区适配，插件本体与协议不变。Tripo Studio 通过本地 WebSocket（`ws://127.0.0.1:60620`）推送 AI 生成的 FBX 模型 + PBR 贴图，编辑器经 Interchange 导入到 `/Game/TripoModels`，材质和贴图自动接好。

**最有意思的一点：C++ 源码零改动。** 插件自带的 `TripoVersionCompat.h` 已经用 `UE_VERSION_AT_LEAST(5, 8)` 门控了 5.8+ 的 Interchange API，5.9 正好满足。唯一需要的修复，是在 `.uplugin` 里补上漏声明的 **Interchange** 插件依赖。

你会得到：

- 开箱即用的 Win64 预编译编辑器二进制（UE 5.9 预览版，BuildId 60351404），也可从源码编译
- WebSocket 导入 FBX + PBR 贴图，自动建 PBR 材质，可选生成到关卡
- 编辑器窗口：实时连接状态、启停控制、传输日志；UI 支持 9 种语言
- 零依赖桥接验证器（`tools/validate_bridge.py`）+ 每次推送都跑的轻量 CI

**验证状态（如实说明）：**

- ✅ 在 UE 5.9 上干净编译，模块在编辑器中成功加载
- ✅ 运行时导入路径已对照 UE 5.9 Interchange 头文件核验
- ✅ 验证器已用忠实还原协议的本地 mock 做过端到端自测
- ⏳ 「从 Tripo Studio 推送 → 导入」的真机全流程在本适配中尚未跑过。用自带验证器几秒即可自查：`--ping-only`（安全、不产生资产）或完整 FBX 导入测试。欢迎反馈结果。

**安装：**

1. 一键下载：[Tripo3DUEBridge-UE5.9-Win64.zip](https://github.com/zty828/Tripo3DUEBridge-UE5.9/releases/download/v1.0.5-ue5.9/Tripo3DUEBridge-UE5.9-Win64.zip)（约 1.9 MB）
2. 解压到工程 `Plugins/` 目录 → `YourProject/Plugins/Tripo3DUEBridge/`
3. 在 Edit → Plugins 启用 **Tripo3D → Tripo Bridge**，重启编辑器
4. 打开 **Window → Tripo Bridge**（服务自动启动），从 Tripo Studio 推送模型

DLL 绑定 5.9 预览版 BuildId **60351404**——若你的 5.9 构建/hotfix 不同，请从源码重编（README 有步骤）。仅 Win64、仅编辑器，不会进打包后的游戏。

**链接：** [仓库](https://github.com/zty828/Tripo3DUEBridge-UE5.9) · [Release v1.0.5-ue5.9](https://github.com/zty828/Tripo3DUEBridge-UE5.9/releases/tag/v1.0.5-ue5.9)

**许可与来源：** 本适配为非官方，与 Tripo3D 无关联、未获其背书。MIT 仅覆盖适配贡献；原插件代码仍版权归 Tripo3D（All Rights Reserved），IXWebSocket 版权归 machinezone（MIT）。商业再分发原代码需 Tripo3D 授权——详见 NOTICE.md。

如果你在 5.9 上试用，欢迎分享真机推送的结果——issue 和 PR 都欢迎。

---

## Pre-posting checklist (review notes — do not post)

- [ ] Confirm the release page and the one-click zip link resolve while logged out.
- [ ] Optional trust detail: zip is 1,892,314 bytes, SHA-256 `E75BC01AF3CB1BAE999E1E6529C7D7410C81B10DEF5636EC69DCA8A7F06F277D`.
- [ ] Keep the "unofficial" label and the licensing paragraph in every version posted.
- [ ] Do not claim the live Tripo Studio → import round-trip is verified; it is header-verified + validator self-tested only.
- [ ] Post once per community (no cross-posting spam); answer questions in-thread.
