# Start the noVNC proxy and open the launcher window (type a host, it opens in its own window).
# Run through mise (`mise run start`) so `python` is the repo .venv.
# The proxy listens on 127.0.0.1 only and reaches any host:port the launcher asks for -- keep it local.
param([int]$port = 6080)

$repo = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$env:PYTHONPATH = $PSScriptRoot

$edge = "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe"
if (Test-Path $edge) {
	Start-Process $edge -ArgumentList "--app=http://localhost:$port/connect.html", '--window-size=480,420'
}

Write-Host "Launcher: http://localhost:$port/connect.html  (Ctrl+C to stop)"
python -m websockify --web $repo --token-plugin anyhost.AnyHost "127.0.0.1:$port"
