#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_bridge.py - end-to-end validator for the Tripo3D UE Bridge (UE 5.9 adaptation).

Pure Python standard library, no third-party dependencies. It speaks the bridge's
WebSocket protocol exactly as implemented in:
  Source/Tripo3DUEBridge/Private/TripoWebSocketServer.cpp
  Source/Tripo3DUEBridge/Private/TripoFileTransferManager.cpp

Protocol facts (verified against the source):
  * A client->server BINARY frame is a JSON header immediately followed by raw chunk
    bytes. The server splits them with a brace-counting JSON scanner (FindJsonEnd).
  * handshake {type, payload:{clientName, protocolVersion}} -> handshake_ack
    (the ack payload carries dccVersion = the running engine version string).
  * ping -> pong
  * file_transfer {payload:{fileId, fileName, fileType, chunkIndex, chunkTotal,
    chunkSize}} + chunk bytes -> file_transfer_ack; once every chunk arrives the
    server emits file_transfer_complete and then import_complete
    {payload:{fileId, success, message}}.

Modes:
  --ping-only   handshake + ping/pong only. NON-DESTRUCTIVE: creates no assets.
                Prints the engine version the editor reports (dccVersion).
  default       full transfer of --fbx, then wait for import_complete. Creates
                assets under /Game/TripoModels in the running editor.

Prerequisite: the UE editor is open with this plugin enabled and the bridge window
open (Window -> Tripo Bridge), which auto-starts ws://127.0.0.1:60620.

Exit codes: 0 = PASS, 2 = import reported failure, 1 = error / timeout.
"""
import argparse
import base64
import hashlib
import json
import os
import socket
import struct
import sys
import time

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
CHUNK = 5 * 1024 * 1024  # matches TripoProtocol::CHUNK_SIZE


def log(*a):
    print("[validate]", *a, flush=True)


class WS:
    """Minimal RFC6455 client (masked client frames, handles server control frames)."""

    def __init__(self, host, port, timeout):
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.sock.settimeout(timeout)
        key = base64.b64encode(os.urandom(16)).decode()
        req = (
            f"GET / HTTP/1.1\r\nHost: {host}:{port}\r\n"
            "Upgrade: websocket\r\nConnection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(req.encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            c = self.sock.recv(1)
            if not c:
                raise RuntimeError("connection closed during HTTP upgrade")
            buf += c
        head, rest = buf.split(b"\r\n\r\n", 1)
        status = head.decode("latin1").split("\r\n")[0]
        if "101" not in status:
            raise RuntimeError("WebSocket upgrade failed: " + status)
        expect = base64.b64encode(hashlib.sha1((key + GUID).encode()).digest()).decode()
        if expect.lower() not in head.decode("latin1").lower():
            raise RuntimeError("Sec-WebSocket-Accept mismatch")
        self._buf = rest

    def _read(self, n):
        while len(self._buf) < n:
            c = self.sock.recv(65536)
            if not c:
                raise RuntimeError("connection closed by server")
            self._buf += c
        out, self._buf = self._buf[:n], self._buf[n:]
        return out

    def send(self, payload, opcode):
        b = bytearray([0x80 | opcode])  # FIN + opcode
        n = len(payload)
        if n < 126:
            b.append(0x80 | n)
        elif n < 65536:
            b.append(0x80 | 126)
            b += struct.pack(">H", n)
        else:
            b.append(0x80 | 127)
            b += struct.pack(">Q", n)
        mask = os.urandom(4)
        b += mask
        b += bytes(x ^ mask[i % 4] for i, x in enumerate(payload))
        self.sock.sendall(bytes(b))

    def send_text(self, s):
        self.send(s.encode("utf-8"), 0x1)

    def send_binary(self, b):
        self.send(b, 0x2)

    def recv(self):
        while True:
            h = self._read(2)
            op = h[0] & 0x0F
            masked = h[1] & 0x80
            n = h[1] & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._read(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._read(8))[0]
            mk = self._read(4) if masked else None
            data = self._read(n) if n else b""
            if mk:
                data = bytes(x ^ mk[i % 4] for i, x in enumerate(data))
            if op == 0x9:  # server ping -> pong
                self.send(data, 0xA)
                continue
            if op == 0xA:  # pong
                continue
            if op == 0x8:
                raise RuntimeError("server sent close frame")
            return op, data

    def wait_type(self, t, timeout):
        end = time.time() + timeout
        while time.time() < end:
            self.sock.settimeout(max(0.5, end - time.time()))
            op, payload = self.recv()
            if op == 0x1:
                try:
                    j = json.loads(payload.decode("utf-8"))
                except Exception:
                    continue
                if j.get("type") == t:
                    return j
        raise RuntimeError("timeout waiting for '" + t + "'")

    def close(self):
        try:
            self.send(b"", 0x8)
        except Exception:
            pass
        self.sock.close()


def main():
    ap = argparse.ArgumentParser(description="Validate the Tripo3D UE Bridge on UE 5.9")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=60620)
    ap.add_argument("--fbx", help="path to a .fbx to import (full mode)")
    ap.add_argument("--ping-only", action="store_true",
                    help="handshake + ping/pong only; creates no assets")
    ap.add_argument("--client-name", default="UE59-Validator")
    ap.add_argument("--expect-engine", default="5.9",
                    help="substring expected in dccVersion; pass '' to skip the check")
    ap.add_argument("--timeout", type=float, default=30.0)
    ap.add_argument("--import-timeout", type=float, default=300.0)
    args = ap.parse_args()

    if not args.ping_only and not args.fbx:
        ap.error("full mode requires --fbx (or use --ping-only)")
    if args.fbx and not os.path.isfile(args.fbx):
        ap.error("FBX not found: " + args.fbx)

    result = {"success": False, "mode": "ping-only" if args.ping_only else "full"}
    ws = None
    try:
        log(f"connecting ws://{args.host}:{args.port} ...")
        ws = WS(args.host, args.port, args.timeout)
        log("WebSocket upgraded")

        ws.send_text(json.dumps({"type": "handshake", "payload": {
            "clientName": args.client_name, "protocolVersion": "1.0.0"}}))
        ack = ws.wait_type("handshake_ack", args.timeout)
        p = ack.get("payload", {})
        if not p.get("success"):
            raise RuntimeError("handshake rejected: " + json.dumps(p))
        engine = p.get("dccVersion", "")
        result["engineVersion"] = engine
        log("handshake OK - editor reports engine:", engine or "(unknown)")
        if args.expect_engine and args.expect_engine not in engine:
            raise RuntimeError(
                f"engine mismatch: expected '{args.expect_engine}' in '{engine}'")

        ws.send_text(json.dumps({"type": "ping"}))
        ws.wait_type("pong", args.timeout)
        log("ping/pong OK")

        if args.ping_only:
            result["success"] = True
            log("PASS (ping-only): bridge alive on", engine)
        else:
            data = open(args.fbx, "rb").read()
            fname = os.path.basename(args.fbx)
            fid = "validate-" + hashlib.md5(data).hexdigest()[:12]
            total = max(1, (len(data) + CHUNK - 1) // CHUNK)
            log(f"transferring {fname}: {len(data)} bytes in {total} chunk(s)")
            for i in range(total):
                sl = data[i * CHUNK:(i + 1) * CHUNK]
                header = json.dumps({"type": "file_transfer", "payload": {
                    "fileId": fid, "fileName": fname, "fileType": "fbx",
                    "chunkIndex": i, "chunkTotal": total, "chunkSize": len(sl)}}).encode("utf-8")
                ws.send_binary(header + sl)
                a = ws.wait_type("file_transfer_ack", args.timeout)
                ap_ = a.get("payload", {})
                if not ap_.get("success"):
                    raise RuntimeError(f"chunk {i} rejected: " + json.dumps(ap_))
                log(f"chunk {i + 1}/{total} acknowledged")
            comp = ws.wait_type("file_transfer_complete", args.timeout)
            log("transfer complete:", comp.get("payload", {}).get("status"))
            done = ws.wait_type("import_complete", args.import_timeout)
            dp = done.get("payload", {})
            result["success"] = bool(dp.get("success"))
            result["message"] = dp.get("message")
            result["fileId"] = fid
            if result["success"]:
                log("PASS: import_complete success -", dp.get("message"))
            else:
                log("FAIL: import_complete reported failure -", dp.get("message"))
        ws.close()
    except Exception as e:
        result["error"] = str(e)
        log("ERROR:", repr(e))
        if ws:
            try:
                ws.close()
            except Exception:
                pass

    print("RESULT_JSON=" + json.dumps(result, ensure_ascii=False), flush=True)
    if result.get("success"):
        sys.exit(0)
    sys.exit(2 if "message" in result else 1)


if __name__ == "__main__":
    main()
