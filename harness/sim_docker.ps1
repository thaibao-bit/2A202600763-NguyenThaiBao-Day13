param(
    [string]$Questions = "",
    [string]$Out = "run_output.json",
    [string]$Phase = "practice",
    [string]$Image = "ubuntu:24.04"
)

$ErrorActionPreference = "Stop"
$repo = (Resolve-Path "$PSScriptRoot\..").Path
$dockerRepo = $repo -replace "\\", "/"

$simBin = "bin/$Phase/observathon-sim"
if (-not (Test-Path (Join-Path $repo $simBin))) {
    throw "Missing Linux simulator: $simBin"
}

$questionArg = ""
if ($Questions) {
    if (-not (Test-Path (Join-Path $repo $Questions))) {
        throw "Missing questions file: $Questions"
    }
    $questionArg = "--questions '$Questions'"
}

docker run --rm `
    -e LOCAL_BASE_URL=http://host.docker.internal:11434/v1 `
    -v "${dockerRepo}:/work" `
    -w /work `
    $Image `
    bash -lc "apt-get update >/dev/null && apt-get install -y python3 python-is-python3 ca-certificates >/dev/null && chmod +x '$simBin' && ./'$simBin' --config solution/config.json --wrapper solution/wrapper.py $questionArg --out '$Out'"
