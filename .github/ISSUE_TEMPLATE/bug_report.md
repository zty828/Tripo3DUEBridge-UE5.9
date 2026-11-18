---
name: Bug report
about: Something does not work on UE 5.9 (or another supported engine)
title: "[Bug] "
labels: bug
---

**Engine version**
e.g. UE 5.9 Preview, BuildId 60351404 (Help → About Unreal Engine).

**Plugin version / commit**
Release tag (e.g. v1.0.5-ue5.9) or the commit SHA you built from.

**OS / toolchain**
e.g. Windows 11, Visual Studio 2022 (MSVC v143), Windows SDK 10.0.22621.

**What happened**
A clear description of the bug.

**Steps to reproduce**
1. ...
2. ...

**Expected behavior**
What you expected to happen.

**Editor log**
Relevant lines from the Output Log (filter `Tripo3D Server` / `LogTemp`). Paste as text.

**Validator output (if relevant)**
Output of `python tools/validate_bridge.py --ping-only` (or full mode), including the
`RESULT_JSON=...` line.

**Additional context**
Screenshots, the FBX used, anything else.
