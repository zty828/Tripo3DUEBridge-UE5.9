# UE 5.9 Adaptation Notes

Technical record of porting the Tripo3D UE Bridge plugin to Unreal Engine 5.9
(Preview). Target engine: `D:\GameEngine\UE_5.9`, `Build.version` 5.9.0,
Changelist / BuildId **60351404**, branch `++UE5+Release-5.9`.

## 1. Why the UE 5.8 binary cannot be reused

The official distribution ships per-engine precompiled variants
(`Tripo3DUEBridge-UE5.4-Win64` … `-UE5.8-Win64`). A UE 5.8 editor DLL is rejected
by UE 5.9 for two independent reasons:

1. **BuildId lock.** `Binaries/Win64/UnrealEditor.modules` records the engine
   BuildId the module was compiled against. The editor only loads modules whose
   BuildId matches the running engine. 5.8 ≠ 5.9 (60351404).
2. **Descriptor pin.** The precompiled variants' `.uplugin` sets
   `EngineVersion` to the matching engine; the pure-source variant omits it.

Conclusion: rebuild from the **pure-source** variant (`Tripo3d_UE_Bridge`,
`.uplugin` without an `EngineVersion` lock).

## 2. Source compatibility — zero C++ changes

The plugin already abstracts engine differences in
`Source/Tripo3DUEBridge/Public/TripoVersionCompat.h`:

```cpp
// UE 5.8+: bSnapToClosestFrameBoundary was replaced by FrameAlignment.
#if UE_VERSION_AT_LEAST(5, 8)
    #define TRIPO_INTERCHANGE_HAS_FRAME_ALIGNMENT 1
#else
    #define TRIPO_INTERCHANGE_HAS_FRAME_ALIGNMENT 0
#endif
```

UE 5.9 satisfies `UE_VERSION_AT_LEAST(5, 8)`, so the importer takes the
`FrameAlignment = EInterchangeFrameAlignment::SnapToClosest` path. Verified
against the UE 5.9 headers:

- `Engine/Plugins/Interchange/Runtime/Source/Pipelines/Public/InterchangeGenericAnimationPipeline.h`
  - L35 `enum class EInterchangeFrameAlignment`
  - L39 `SnapToClosest`
  - L93 `FrameAlignment` member
  - L96 `bSnapToClosestFrameBoundary_DEPRECATED`
- `InterchangeGenericAssetsPipeline.h` L101 `AnimationPipeline`

Other version gates (FBX scale factor, `FAppStyle`, material search location,
UE 5.4 skeletal-scale fix) all resolve correctly for 5.9. **No `.cpp`/`.h`
logic was edited.**

## 3. The one packaging fix

The module's `Build.cs` lists `InterchangeEngine` and `InterchangePipelines`
as private dependencies, but the original `.uplugin` did not declare the
**Interchange** plugin. UBT warned about the undeclared plugin dependency. Fix —
add to `Tripo3DUEBridge.uplugin`:

```json
"Plugins": [
  { "Name": "Interchange", "Enabled": true }
]
```

This is the only functional change to the plugin package.

## 4. Build configuration

`Source/Tripo3DUEBridge/Tripo3DUEBridge.Build.cs`:

- `bPrecompile = true`, `PrecompileForTargets = Any` (Blueprint projects can use
  the precompiled binary).
- Links `ThirdParty/IXWebSocket/Lib/Win64/IXWebSocket.lib` (required; throws if
  missing) and defines `IXWEBSOCKET_USE_PRECOMPILED=1`.
- Auto-detects the engine's zlib. For UE 5.7+ it probes only `1.3`; UE 5.9 ships
  zlib 1.3 at `Engine/Source/ThirdParty/zlib/1.3`, links
  `lib/Win64/Release/zlibstatic.lib`, defines `IXWEBSOCKET_USE_ZLIB=1`.
- Win64 system libs: `ws2_32.lib`, `crypt32.lib`, `iphlpapi.lib`.
- Module dependencies include `InterchangeEngine`, `InterchangePipelines`,
  `FBX`, `WebSockets`, `UnrealEd`, `MaterialEditor`, etc.

Toolchain used: Visual Studio 2022 (MSVC 14.44.35207), Windows SDK 10.0.22621.

## 5. Verification

- **Host C++ project build** (`BuildSettingsVersion.V8`,
  `EngineIncludeOrderVersion.Unreal5_9`): **Succeeded**. All 9 Tripo translation
  units compiled; DLL linked; BuildId 60351404.
- **Runtime module load** (host editor log):
  `LogModuleManager: InternalLoadLibrary 'Tripo3DUEBridge'` and
  `Tripo Bridge module started successfully`.
- **Main project build** (alongside PICOOpenXR / OpenXR plugins): **Succeeded**,
  BuildId 60351404, no module conflicts.

> Gotcha: an open editor holds the engine-wide Live Coding lock. Building while
> any editor is running fails with
> `Unable to build while Live Coding is active`. Close all editors first.

## 6. What is shipped

- Full source (`Source/`, `ThirdParty/`, `Content/`, `Config/`, `Resources/`).
- `Tripo3DUEBridge.uplugin` with the Interchange dependency.
- Precompiled `Binaries/Win64/UnrealEditor-Tripo3DUEBridge.dll` (+ `.modules`,
  `.uclasses`) for UE 5.9 BuildId 60351404. **PDB and Intermediate are excluded.**

## 7. Not yet automated

The end-to-end "open window → push from Tripo Studio → import" path was verified
by compilation + module load + API/header review, but the live push was not
automated in this port. To validate manually: open **Window → Tripo Bridge**
(server auto-starts on `ws://127.0.0.1:60620`) and push a model from Tripo Studio.
