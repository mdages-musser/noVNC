"""Run websockify with `Cache-Control: no-cache` on every web response.

websockify's file server sends no cache headers, so browsers keep heuristically cached copies of
noVNC's JS after the files change (e.g. after switching branches), and run a mismatched ui.js
against a newer vnc.html. no-cache makes the browser revalidate each file (cheap 304s).
Takes the same arguments as `python -m websockify`.
"""
from websockify import websocketproxy


class NoCacheProxyRequestHandler(websocketproxy.ProxyRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


websocketproxy.ProxyRequestHandler = NoCacheProxyRequestHandler
websocketproxy.WebSocketProxy.__init__.__defaults__ = (NoCacheProxyRequestHandler,)

if __name__ == "__main__":
    websocketproxy.websockify_init()
