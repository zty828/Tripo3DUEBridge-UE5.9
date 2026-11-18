# NOTICE — Provenance & Third-Party Attributions

This repository is an **unofficial community adaptation** of the Tripo3D UE Bridge
plugin for Unreal Engine 5.9. It is not affiliated with, endorsed by, or sponsored
by Tripo3D.

## Original work

- **Tripo3D UE Bridge** — Copyright Tripo3D. All Rights Reserved.
  - Source: https://www.tripo3d.ai
  - The overwhelming majority of the C++ source, content assets, localization,
    and design in this repository is the original Tripo3D work, used here under
    its original terms. Upstream copyright headers (e.g.
    `// Copyright Tripo3D. All Rights Reserved.`) are preserved verbatim in the
    source files.
  - This repository does **not** relicense the original Tripo3D code.

## Adaptation contributions

- UE 5.9 adaptation — Copyright (c) 2026 zty828 and contributors.
  - Scope: packaging/descriptor fixes (declaring the Interchange plugin
    dependency in `Tripo3DUEBridge.uplugin`), build verification against
    UE 5.9, the precompiled Win64 editor binary, and the documentation in this
    repository. No C++ source logic was modified.
  - These adaptation contributions are released under the MIT License (see
    `LICENSE`). The MIT grant applies **only** to these contributions and does
    **not** extend to the original Tripo3D code or to third-party components.

## Third-party components

- **IXWebSocket** — Copyright (c) machinezone. MIT License.
  - Source: https://github.com/machinezone/IXWebSocket
  - Bundled as headers + precompiled `ThirdParty/IXWebSocket/Lib/Win64/IXWebSocket.lib`.
- **minizip** — part of the zlib distribution.
  - Source: https://www.zlib.net
  - Bundled headers under `Source/Tripo3DUEBridge/Private/minizip/`; links the
    Unreal Engine's built-in zlib at build time.
- **Unreal Engine** — Copyright Epic Games, Inc. The plugin builds against and
  runs inside Unreal Engine and is subject to Epic's Unreal Engine EULA. The
  `Build.cs` carries the standard Epic Games template header.

## Redistribution note

Because the original plugin is "All Rights Reserved", redistributing this
adaptation (especially commercially) may require permission from Tripo3D. This
repository is provided for interoperability with UE 5.9; verify upstream terms
before redistribution.
