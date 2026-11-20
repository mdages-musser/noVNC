"""Read a VNC server's native pixel format and test whether it honours SetPixelFormat.

Usage: python vncfmt.py host[:port] [password]   (port defaults to 5900)

B&R VC4 servers report BGRX and ignore SetPixelFormat; the frames requested in RGBX and
BGRX layouts then come back byte-for-byte identical. That is what core/rfb.js works around.
"""
import socket
import struct
import sys

from Crypto.Cipher import DES

DEFAULT_PORT = 5900


def recv_exact(s: socket.socket, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = s.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("closed")
        buf += chunk
    return buf


def reverse_bits(b: int) -> int:
    return int(f"{b:08b}"[::-1], 2)


def pixel_format(rsh: int, gsh: int, bsh: int) -> bytes:
    """32 bpp, depth 24, little-endian true colour with the given shifts."""
    return struct.pack(">BBBBHHHBBB3x", 32, 24, 0, 1, 255, 255, 255, rsh, gsh, bsh)


def grab(s: socket.socket, w: int, h: int, fmt: bytes) -> bytes:
    """Set a pixel format, request a full non-incremental Raw frame, return its pixel bytes."""
    s.sendall(b"\x00\x00\x00\x00" + fmt)
    s.sendall(struct.pack(">BxHi", 2, 1, 0))  # SetEncodings: Raw only
    s.sendall(struct.pack(">BBHHHH", 3, 0, 0, 0, w, h))
    while True:
        msg = recv_exact(s, 1)[0]
        if msg == 0:
            break
        if msg != 2:  # 2 = bell, ignore
            raise RuntimeError(f"unexpected message {msg}")
    recv_exact(s, 1)
    count = struct.unpack(">H", recv_exact(s, 2))[0]
    data = bytearray(w * h * 4)
    for _ in range(count):
        x, y, rw, rh, enc = struct.unpack(">HHHHi", recv_exact(s, 12))
        if enc != 0:
            raise RuntimeError(f"server sent encoding {enc}")
        raw = recv_exact(s, rw * rh * 4)
        for row in range(rh):
            start = ((y + row) * w + x) * 4
            data[start:start + rw * 4] = raw[row * rw * 4:(row + 1) * rw * 4]
    return bytes(data)


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    host, _, port = sys.argv[1].rpartition(":")
    if not host:
        host, port = port, str(DEFAULT_PORT)
    password = sys.argv[2] if len(sys.argv) > 2 else ""

    s = socket.create_connection((host, int(port)), 5)
    version = recv_exact(s, 12)
    s.sendall(b"RFB 003.003\n")
    sec = struct.unpack(">I", recv_exact(s, 4))[0]
    if sec == 0:
        sys.exit("connection refused by server")
    if sec == 2:
        challenge = recv_exact(s, 16)
        key = bytes(reverse_bits(c) for c in password.encode()[:8].ljust(8, b"\0"))
        s.sendall(DES.new(key, DES.MODE_ECB).encrypt(challenge))
        if struct.unpack(">I", recv_exact(s, 4))[0]:
            sys.exit("auth: FAILED (wrong password?)")
        print("auth: ok")
    s.sendall(b"\x01")  # shared: do not kick other clients
    init = recv_exact(s, 24)
    w, h = struct.unpack(">HH", init[:4])
    bpp, depth, big, true, rmax, gmax, bmax, rsh, gsh, bsh = struct.unpack(">BBBBHHHBBB3x", init[4:20])
    name = recv_exact(s, struct.unpack(">I", init[20:24])[0]).decode(errors="replace")
    print(f"{version.strip().decode()} '{name}' {w}x{h}")
    print(f"native: bpp={bpp} depth={depth} bigEndian={big} trueColor={true} "
          f"max=({rmax},{gmax},{bmax}) shift r={rsh} g={gsh} b={bsh}")

    rgb = grab(s, w, h, pixel_format(0, 8, 16))   # what noVNC requests
    bgr = grab(s, w, h, pixel_format(16, 8, 0))
    coloured = sum(1 for i in range(0, len(rgb), 4) if rgb[i] != rgb[i + 2])
    print(f"pixels with red != blue: {coloured}")
    if not coloured:
        print("honours SetPixelFormat: unknown (screen has no red/blue content to compare)")
    else:
        print("honours SetPixelFormat:", "NO (identical bytes)" if rgb == bgr else "yes (bytes differ)")
    s.close()


if __name__ == "__main__":
    main()
