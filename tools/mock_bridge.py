#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mock_bridge.py - faithful, dependency-free mock of the Tripo3D UE Bridge WebSocket
protocol, for testing tools/validate_bridge.py WITHOUT Unreal Engine.

Mirrors Source/Tripo3DUEBridge/Private/TripoWebSocketServer.cpp and
TripoFileTransferManager.cpp: JSON control frames plus binary frames that are a JSON
header followed by raw chunk bytes (split with a brace-counting scanner).

Run standalone:  python tools/mock_bridge.py --port 60621 --stats stats.jsonl
Or import and call serve() in a thread (see tools/selftest.py).

Each completed import appends one JSON line to --stats:
  {"fileId": ..., "name": ..., "bytes": ..., "chunks": ..., "sha256": ...}
so a test can assert end-to-end integrity across chunks.
"""
import argparse
import base64
import hashlib
import json
import socket
import struct
import threading

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
ENGINE_VERSION = "5.9.0-60351404-mock"
_stats_lock = threading.Lock()


def recv_exact(c, n):
    b = b""
    while len(b) < n:
        x = c.recv(n - len(b))
        if not x:
            raise ConnectionError("closed")
        b += x
    return b


def read_frame(c):
    h = recv_exact(c, 2)
    op = h[0] & 0x0F
    masked = h[1] & 0x80
    n = h[1] & 0x7F
    if n == 126:
        n = struct.unpack(">H", recv_exact(c, 2))[0]
    elif n == 127:
        n = struct.unpack(">Q", recv_exact(c, 8))[0]
    mk = recv_exact(c, 4) if masked else None
    data = recv_exact(c, n) if n else b""
    if mk:
        data = bytes(x ^ mk[i % 4] for i, x in enumerate(data))
    return op, data


def send_frame(c, payload, op):
    b = bytearray([0x80 | op])
    n = len(payload)
    if n < 126:
        b.append(n)
    elif n < 65536:
        b.append(126)
        b += struct.pack(">H", n)
    else:
        b.append(127)
        b += struct.pack(">Q", n)
    c.sendall(bytes(b) + payload)


def send_json(c, obj):
    send_frame(c, json.dumps(obj).encode("utf-8"), 0x1)


def find_json_end(data):
    depth = 0
    ins = False
    esc = False
    for i, by in enumerate(data):
        if by >= 128:
            continue
        ch = chr(by)
        if esc:
            esc = False
            continue
        if ch == "\\":
            esc = True
            continue
        if ch == '"':
            ins = not ins
            continue
        if not ins:
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return i + 1
    return -1


def handle(c, stats_path):
    buf = b""
    while b"\r\n\r\n" not in buf:
        buf += recv_exact(c, 1)
    key = ""
    for line in buf.decode("latin1").split("\r\n"):
        if line.lower().startswith("sec-websocket-key:"):
            key = line.split(":", 1)[1].strip()
    accept = base64.b64encode(hashlib.sha1((key + GUID).encode()).digest()).decode()
    c.sendall(("HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\n"
               "Connection: Upgrade\r\nSec-WebSocket-Accept: " + accept + "\r\n\r\n").encode())
    sessions = {}
    while True:
        op, data = read_frame(c)
        if op == 0x8:
            break
        if op == 0x9:
            send_frame(c, data, 0xA)
            continue
        if op == 0x1:
            j = json.loads(data.decode("utf-8"))
            t = j.get("type")
            if t == "handshake":
                send_json(c, {"type": "handshake_ack", "payload": {
                    "success": True, "clientName": "Unreal Engine",
                    "dccVersion": ENGINE_VERSION, "pluginVersion": "1.0.0",
                    "protocolVersion": "1.0.0"}})
            elif t == "ping":
                send_json(c, {"type": "pong"})
        elif op == 0x2:
            je = find_json_end(data)
            j = json.loads(data[:je].decode("utf-8"))
            chunk = data[je:]
            p = j.get("payload", {})
            fid = p["fileId"]
            idx = p["chunkIndex"]
            tot = p["chunkTotal"]
            s = sessions.setdefault(fid, {"name": p["fileName"], "chunks": {}, "total": tot})
            s["chunks"][idx] = chunk
            send_json(c, {"type": "file_transfer_ack", "payload": {
                "success": True, "fileId": fid, "fileIndex": idx, "code": 0}})
            if len(s["chunks"]) == tot:
                send_json(c, {"type": "file_transfer_complete", "payload": {
                    "fileId": fid, "status": "importing",
                    "message": "File transfer complete, importing " + s["name"] + "..."}})
                assembled = b"".join(s["chunks"][i] for i in range(tot))
                ok = len(assembled) > 0
                if stats_path:
                    rec = {"fileId": fid, "name": s["name"], "bytes": len(assembled),
                           "chunks": tot, "sha256": hashlib.sha256(assembled).hexdigest()}
                    with _stats_lock:
                        with open(stats_path, "a", encoding="utf-8") as f:
                            f.write(json.dumps(rec) + "\n")
                send_json(c, {"type": "import_complete", "payload": {
                    "fileId": fid, "success": ok,
                    "message": ("Import complete: " if ok else "Import failed: ") + s["name"]}})
                del sessions[fid]
    c.close()


def serve(port, stats_path=None, ready=None):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", port))
    srv.listen(5)
    if ready is not None:
        ready.set()
    while True:
        c, _ = srv.accept()
        try:
            handle(c, stats_path)
        except Exception:
            try:
                c.close()
            except Exception:
                pass


def main():
    ap = argparse.ArgumentParser(description="Mock Tripo bridge WS server (no UE)")
    ap.add_argument("--port", type=int, default=60621)
    ap.add_argument("--stats", default=None)
    a = ap.parse_args()
    print("[mock] listening on 127.0.0.1:%d" % a.port, flush=True)
    serve(a.port, a.stats)


if __name__ == "__main__":
    main()
