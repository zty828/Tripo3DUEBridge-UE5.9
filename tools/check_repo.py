#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_repo.py - lightweight repository structure check. NO Unreal Engine required.

Run locally:  python tools/check_repo.py
Used by:      .github/workflows/validate.yml

Verifies the drop-in plugin layout, the .uplugin manifest (modules + the Interchange
plugin dependency that the UE 5.9 adaptation added), license/provenance files, the
precompiled editor binary, and that no build intermediates or PDBs were committed.
Exits non-zero on any failure.
"""
import json
import os
import py_compile
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
errors = []


def check(cond, msg):
    print(("PASS" if cond else "FAIL"), "-", msg)
    if not cond:
        errors.append(msg)


def exists(rel):
    return os.path.isfile(os.path.join(ROOT, rel))


REQUIRED = [
    "Tripo3DUEBridge.uplugin",
    "Source/Tripo3DUEBridge/Tripo3DUEBridge.Build.cs",
    "Source/Tripo3DUEBridge/Private/TripoWebSocketServer.cpp",
    "Source/Tripo3DUEBridge/Private/TripoFileTransferManager.cpp",
    "Source/Tripo3DUEBridge/Public/TripoVersionCompat.h",
    "Source/Tripo3DUEBridge/Public/TripoProtocol.h",
    "ThirdParty/IXWebSocket/Lib/Win64/IXWebSocket.lib",
    "Binaries/Win64/UnrealEditor-Tripo3DUEBridge.dll",
    "Binaries/Win64/UnrealEditor.modules",
    "README.md",
    "NOTICE.md",
    "LICENSE",
    "docs/ADAPTATION.md",
    "VALIDATION.md",
    "tools/validate_bridge.py",
    "tools/mock_bridge.py",
    "tools/selftest.py",
]
for r in REQUIRED:
    check(exists(r), "required file present: " + r)

# .uplugin manifest sanity
try:
    with open(os.path.join(ROOT, "Tripo3DUEBridge.uplugin"), encoding="utf-8") as f:
        up = json.load(f)
    mods = up.get("Modules", [])
    check(isinstance(mods, list) and len(mods) > 0, ".uplugin declares at least one module")
    check(any(m.get("Name") == "Tripo3DUEBridge" for m in mods),
          ".uplugin declares the Tripo3DUEBridge module")
    plugins = up.get("Plugins", [])
    check(any(p.get("Name") == "Interchange" and p.get("Enabled", False) for p in plugins),
          ".uplugin declares the Interchange plugin dependency (UE 5.9 adaptation fix)")
except Exception as e:
    check(False, ".uplugin parses as JSON: " + repr(e))

# precompiled binary non-empty
dll = os.path.join(ROOT, "Binaries/Win64/UnrealEditor-Tripo3DUEBridge.dll")
check(os.path.isfile(dll) and os.path.getsize(dll) > 0, "editor DLL is present and non-empty")

# validator is syntactically valid Python
try:
    py_compile.compile(os.path.join(ROOT, "tools/validate_bridge.py"), doraise=True)
    check(True, "tools/validate_bridge.py compiles")
except Exception as e:
    check(False, "tools/validate_bridge.py compiles: " + repr(e))

for t in ("tools/mock_bridge.py", "tools/selftest.py"):
    try:
        py_compile.compile(os.path.join(ROOT, t), doraise=True)
        check(True, t + " compiles")
    except Exception as e:
        check(False, t + " compiles: " + repr(e))

# no build intermediates / PDBs committed
try:
    tracked = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()
    bad = [p for p in tracked
           if p.lower().endswith(".pdb")
           or p.startswith("Intermediate/")
           or p.startswith("Saved/")
           or p.lower().endswith(".exp")]
    check(not bad, "no PDB / Intermediate / Saved artifacts committed" + (": " + ", ".join(bad) if bad else ""))
except Exception as e:
    print("WARN - could not run git ls-files (skipping artifact check):", repr(e))

print()
if errors:
    print(f"RESULT: FAIL ({len(errors)} problem(s))")
    sys.exit(1)
print("RESULT: PASS")
