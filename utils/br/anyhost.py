"""websockify token plugin: the token IS the target, as "host" or "host:port" (default port 5900).

Lets the launcher page connect to any VNC server without a token file. Only safe because
start-novnc.ps1 binds websockify to 127.0.0.1 -- never expose this proxy on the network.
"""
from websockify.token_plugins import BasePlugin

DEFAULT_PORT = 5900


class AnyHost(BasePlugin):
    def lookup(self, token: str) -> tuple[str, int] | None:
        host, _, port = token.strip().rpartition(":")
        if not host:  # no colon: the whole token is the host
            host, port = port, str(DEFAULT_PORT)
        if not host or not port.isdigit() or not 0 < int(port) < 65536:
            return None
        return host, int(port)
