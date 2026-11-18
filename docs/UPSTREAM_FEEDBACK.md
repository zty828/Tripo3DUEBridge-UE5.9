# Upstream Feedback — DRAFT (NOT submitted)

> **Status: DRAFT — nothing in this file has been submitted to Tripo3D or posted anywhere.**
> Intended recipient: maintainers of the official Tripo3D UE Bridge plugin.
> Where to post: to be confirmed by the repo owner — Tripo3D official support / community channels, or an upstream GitHub issue tracker if one is public. No upstream repo URL is assumed here.
> Contents: (1) GitHub-style issue draft, (2) optional short PR description for the one-line fix, (3) optional Chinese courtesy translation.

---

## 1. Draft GitHub issue

**Title:** UE 5.9 Preview: the source is already compatible — only the Interchange dependency declaration is missing in `.uplugin`

**Body:**

Hello Tripo3D team,

Thank you for the UE Bridge plugin — it makes the Tripo Studio → Unreal workflow genuinely pleasant. I recently needed it on **Unreal Engine 5.9 Preview** (BuildId 60351404), and I'd like to share what I found, offer the adaptation, and ask one licensing question.

### Compatibility findings

1. **The existing version gate already covers 5.9.** `Source/Tripo3DUEBridge/Public/TripoVersionCompat.h` gates the Interchange animation API change (`bSnapToClosestFrameBoundary` → `FrameAlignment`) behind `UE_VERSION_AT_LEAST(5, 8)`. UE 5.9 satisfies that gate; I verified the `FrameAlignment` / `EInterchangeFrameAlignment::SnapToClosest` path against the 5.9 headers (`InterchangeGenericAnimationPipeline.h`). **No C++ source changes were required.**
2. **One packaging fix was needed.** `Tripo3DUEBridge.Build.cs` lists `InterchangeEngine` and `InterchangePipelines` as dependencies, but the `.uplugin` does not declare the **Interchange** plugin, which produces a UBT undeclared-plugin-dependency warning. Adding this to `Tripo3DUEBridge.uplugin` resolves it:

   ```json
   "Plugins": [
     { "Name": "Interchange", "Enabled": true }
   ]
   ```

   With that single change, the pure-source variant builds cleanly (VS2022 / MSVC 14.44, Windows SDK 10.0.22621, engine zlib 1.3) and the editor module loads on 5.9 (`Tripo Bridge module started successfully`).
3. As expected, the precompiled 5.4–5.8 variants are rejected by 5.9 (BuildId in `UnrealEditor.modules` plus the `EngineVersion` pin). An official 5.9 precompiled variant would be a big help for users who don't build from source.

### Verification status (honest)

- Build + runtime module load: verified on UE 5.9 Preview.
- Import API usage: verified against the UE 5.9 Interchange headers.
- Protocol: a dependency-free validator (handshake / ping / chunked FBX transfer / `import_complete`) was self-tested against a faithful protocol mock. A live Tripo Studio push on 5.9 is still pending.

### Offer

I published the adaptation as an explicitly **unofficial** community repo, with upstream copyright headers preserved verbatim:

- Repository: https://github.com/zty828/Tripo3DUEBridge-UE5.9
- Release (precompiled Win64 for 5.9): https://github.com/zty828/Tripo3DUEBridge-UE5.9/releases/tag/v1.0.5-ue5.9

The functional change set is descriptor-only (the `.uplugin` fix above). I'm happy to contribute that fix upstream, share the build notes, or hand over the validator if any of it helps you ship an official 5.9 variant. No affiliation or endorsement is claimed.

### Licensing clarification (polite ask)

The original plugin is marked "Copyright Tripo3D. All Rights Reserved." My repo states clearly that its MIT license covers **only** the adaptation contributions and does not relicense the original code (see `NOTICE.md`). Could you clarify:

1. Whether non-commercial community redistribution of the adapted package (original code + descriptor fix + rebuilt 5.9 binary) is acceptable under your terms;
2. Any attribution, branding, or distribution conditions you would like me to follow;
3. The right contact or path for commercial redistribution licensing.

I will follow your guidance — including adjusting or removing the public repo if you prefer.

Thank you for the great tool, and for considering this.

---

## 2. Optional short PR description (if upstream accepts pull requests)

**Title:** Declare Interchange plugin dependency in `.uplugin`

**Body:**

`Tripo3DUEBridge.Build.cs` depends on `InterchangeEngine` / `InterchangePipelines`, but the plugin descriptor never declares the **Interchange** plugin, so UBT emits an undeclared-plugin-dependency warning. This adds the declaration:

```json
"Plugins": [
  { "Name": "Interchange", "Enabled": true }
]
```

No C++ changes. Verified on UE 5.9 Preview (BuildId 60351404): clean build and successful editor module load. The existing `UE_VERSION_AT_LEAST(5, 8)` compatibility path in `TripoVersionCompat.h` already covers 5.9, so this descriptor fix is the only change needed for 5.9 support.

---

## 3. Optional Chinese courtesy translation (issue draft)

**标题：** UE 5.9 预览版兼容性反馈：源码本身已兼容，仅 `.uplugin` 缺少 Interchange 依赖声明

Tripo3D 团队好：

感谢 UE Bridge 插件。我在 **UE 5.9 预览版**（BuildId 60351404）上使用时的发现如下：

1. **现有版本门控已覆盖 5.9。** `TripoVersionCompat.h` 用 `UE_VERSION_AT_LEAST(5, 8)` 门控 Interchange 动画 API 变化（`bSnapToClosestFrameBoundary` → `FrameAlignment`），5.9 满足该条件；已对照 5.9 头文件核验 `FrameAlignment` / `EInterchangeFrameAlignment::SnapToClosest` 路径。**C++ 源码无需任何改动。**
2. **唯一需要的是打包修复。** `Build.cs` 依赖 `InterchangeEngine` / `InterchangePipelines`，但 `.uplugin` 未声明 **Interchange** 插件，UBT 会报未声明插件依赖警告。补上 `"Plugins": [{ "Name": "Interchange", "Enabled": true }]` 即可。仅此一处改动，纯源码变体即可干净编译（VS2022 / MSVC 14.44）并在 5.9 编辑器中成功加载模块。
3. 5.4–5.8 预编译变体因 BuildId 与 EngineVersion 锁定无法在 5.9 加载（符合预期）；如官方能出 5.9 预编译变体，对不自行编译的用户会很有帮助。

验证状态（如实）：编译 + 模块加载已实测；导入 API 已对照 5.9 头文件核验；协议验证器已用忠实 mock 自测；Tripo Studio 真机推送尚待验证。

我已将适配以明确标注**非官方**的社区仓库发布（保留上游版权头）：
仓库 https://github.com/zty828/Tripo3DUEBridge-UE5.9 · Release https://github.com/zty828/Tripo3DUEBridge-UE5.9/releases/tag/v1.0.5-ue5.9
功能性改动仅为上述描述符修复。乐意向上游贡献该修复、提供编译记录或验证器，协助官方推出 5.9 变体。

**许可咨询：** 原插件为 All Rights Reserved；我的仓库已声明 MIT 仅覆盖适配贡献、不对上游代码重新授权（见 NOTICE.md）。想确认：① 非商业社区再分发适配包（原代码 + 描述符修复 + 重编二进制）是否被允许；② 是否有署名/品牌/分发条件需要遵守；③ 商业再分发授权的联络渠道。我会遵从贵方意见，包括在必要时调整或下架仓库。

感谢你们的优秀工具！
