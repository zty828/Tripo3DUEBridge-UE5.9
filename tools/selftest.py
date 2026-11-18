#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selftest.py - end-to-end self-test of tools/validate_bridge.py against the faithful
mock bridge (tools/mock_bridge.py). NO Unreal Engine required; runs in CI.

Covers: ping-only, single-chunk import, MULTI-chunk import (>5MiB, exercising the
chunked send/reassemble path), and a negative engine-version case. Asserts the mock's
reassembled SHA-256 equals the source payload (end-to-end integrity across chunks).

Run:  python tools/selftest.py     (exit 0 = all pass)
"""
import hashlib
import json
import os
import struct
import subprocess
import sys
import tempfile
import threading
import time

import mock_bridge

HERE = os.path.dirname(os.path.abspath(__file__))
VALIDATOR = os.path.join(HERE, "validate_bridge.py")
PORT = 60621
CHUNK = 5 * 1024 * 1024


def sha(b):
    return hashlib.sha256(b).hexdigest()


def make_payload(n):
    out = bytearray()
    x = 123456789
    while len(out) < n:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        out += struct.pack("<I", x)
    return bytes(out[:n])


def run_validator(args):
    r = subprocess.run([sys.executable, VALIDATOR] + args, capture_output=True, text=True)
    return r.returncode


def main():
    tmp = tempfile.mkdtemp(prefix="tripo_selftest_")
    stats = os.path.join(tmp, "stats.jsonl")
    small = make_payload(200 * 1024)              # 1 chunk
    large = make_payload(12 * 1024 * 1024 + 123)  # 3 chunks (5+5+2 MiB, unaligned tail)
    small_p = os.path.join(tmp, "small.fbx")
    large_p = os.path.join(tmp, "large.fbx")
    with open(small_p, "wb") as f:
        f.write(small)
    with open(large_p, "wb") as f:
        f.write(large)

    ready = threading.Event()
    th = threading.Thread(target=mock_bridge.serve, args=(PORT, stats, ready), daemon=True)
    th.start()
    if not ready.wait(5):
        print("SELFTEST=" + json.dumps({"pass": False, "error": "mock did not start"}))
        return 1
    time.sleep(0.2)

    exits = {}
    exits["ping_only"] = run_validator(["--ping-only", "--port", str(PORT), "--expect-engine", "5.9"])
    exits["single_chunk"] = run_validator(["--fbx", small_p, "--port", str(PORT)])
    exits["multi_chunk"] = run_validator(["--fbx", large_p, "--port", str(PORT)])
    exits["wrong_engine"] = run_validator(["--ping-only", "--port", str(PORT), "--expect-engine", "5.8"])

    entries = []
    if os.path.isfile(stats):
        with open(stats, encoding="utf-8") as f:
            entries = [json.loads(l) for l in f if l.strip()]
    by_sha = {e["sha256"]: e for e in entries}
    small_ok = sha(small) in by_sha and by_sha[sha(small)]["chunks"] == 1
    large_ok = sha(large) in by_sha and by_sha[sha(large)]["chunks"] == (len(large) + CHUNK - 1) // CHUNK

    ok = (exits["ping_only"] == 0 and exits["single_chunk"] == 0
          and exits["multi_chunk"] == 0 and exits["wrong_engine"] == 1
          and small_ok and large_ok)
    print("SELFTEST=" + json.dumps({
        "exits": exits,
        "single_chunk_integrity": small_ok,
        "multi_chunk_integrity": large_ok,
        "multi_chunk_count": by_sha.get(sha(large), {}).get("chunks"),
        "pass": ok}))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
