# B&R VNC tooling

Fork-local tools for viewing B&R VC4 visualizations (ARsim or a real target) through noVNC.

| Command | What it does |
|---|---|
| `mise install` | Installs the pinned Python and creates `.venv` |
| `mise run start` | Starts websockify on `127.0.0.1:6080` and opens `connect.html` in an Edge app window |
| `mise run probe -- 127.0.0.1:5902 1` | Prints a server's native pixel format and whether it honours SetPixelFormat |

| File | Purpose |
|---|---|
| `../../connect.html` | Launcher: host box, recent targets; each target opens in its own window |
| `anyhost.py` | websockify token plugin: the `token` URL parameter is the target `host[:port]` (default 5900) |
| `vncfmt.py` | The pixel-format probe |
| `serve.py` | Runs websockify with `Cache-Control: no-cache`, so browsers never run stale noVNC JS |
| `start.ps1` | What `mise run start` runs |

Bookmark a target directly:
`http://127.0.0.1:6080/vnc.html?host=127.0.0.1&port=6080&autoconnect=1&resize=scale&show_dot=true&path=websockify%3Ftoken%3D127.0.0.1%3A5902`

## B&R quirks handled in `core/`

- **Red/blue swapped.** The VC4 server reports BGRX and ignores SetPixelFormat. `rfb.js` detects it
  (name `VC Project ...`, 32 bpp, red shift 16, blue shift 0) and `display.js` swaps the two bytes when drawing.
- **No cursor.** The server sends no cursor image; `connect.html` sets `show_dot=true`.

## Safety

The proxy connects to whatever host the URL names. It must only listen on `127.0.0.1`.
