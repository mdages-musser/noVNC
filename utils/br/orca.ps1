# Open a VNC target inline in an Orca browser tab, starting the proxy first if it isn't running.
# Run through mise (`mise run orca -- 127.0.0.1:5903`) so `python` is the repo .venv.
# The password, if given, rides in the tab's URL -- fine on 127.0.0.1, but leave it off to be prompted instead.
param(
	[string]$target = '127.0.0.1:5902',
	[string]$password = '',
	[ValidateSet('2', '6', '9')][string]$quality = '6',
	[int]$port = 6080
)

$repo = Resolve-Path (Join-Path $PSScriptRoot '..\..')

if (-not (Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort $port -State Listen -ErrorAction SilentlyContinue)) {
	$env:PYTHONPATH = $PSScriptRoot
	$serve = Join-Path $PSScriptRoot 'serve.py'
	Start-Process (Get-Command python).Source -WindowStyle Hidden -ArgumentList `
		"`"$serve`"", '--web', "`"$repo`"", '--token-plugin', 'anyhost.AnyHost', "127.0.0.1:$port"
	$deadline = (Get-Date).AddSeconds(10)
	while (-not (Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort $port -State Listen -ErrorAction SilentlyContinue)) {
		if ((Get-Date) -gt $deadline) { throw "Proxy did not start on 127.0.0.1:$port" }
		Start-Sleep -Milliseconds 250
	}
	Write-Host "Proxy started on 127.0.0.1:$port"
}

$query = @(
	'host=127.0.0.1'
	"port=$port"
	'path=' + [uri]::EscapeDataString("websockify?token=$target")
	'autoconnect=1'
	'resize=scale'
	'show_dot=true'
	"quality=$quality"
)
if ($password) { $query += 'password=' + [uri]::EscapeDataString($password) }
$url = "http://127.0.0.1:$port/vnc.html?" + ($query -join '&')

orca tab create --url $url --json | Out-Null
Write-Host "Opened $target in Orca"
