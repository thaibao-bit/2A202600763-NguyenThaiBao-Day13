param(
    [string]$Questions = "",
    [string]$Out = "run_output.json"
)

$ErrorActionPreference = "Stop"
$repo = (Resolve-Path "$PSScriptRoot\..").Path
Set-Location $repo

$env:LOCAL_BASE_URL = "http://localhost:11434/v1"
$env:PYTHONIOENCODING = "utf-8"

try {
    Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 3 | Out-Null
} catch {
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 3
}

ollama list | Out-Null

$questionArg = @()
if ($Questions) {
    if (-not (Test-Path $Questions)) {
        throw "Missing questions file: $Questions"
    }
    $questionArg = @("--questions", $Questions)
}

& ".\bin\practice\observathon-sim.exe" `
    --config "solution\config.json" `
    --wrapper "solution\wrapper.py" `
    @questionArg `
    --out $Out
