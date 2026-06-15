param(
    [string]$Team = "NguyenThaiBao",
    [string]$Run = "run_output.json",
    [string]$Findings = "solution/findings.json",
    [string]$Out = "score.json",
    [string]$Phase = "practice",
    [string]$Image = "ubuntu:24.04"
)

$ErrorActionPreference = "Stop"

$repo = (Resolve-Path "$PSScriptRoot\..").Path
$dockerRepo = $repo -replace "\\", "/"

if (-not (Test-Path (Join-Path $repo $Run))) {
    throw "Missing run file: $Run. Run observathon-sim first."
}

$scoreBin = "bin/$Phase/observathon-score"
if (-not (Test-Path (Join-Path $repo $scoreBin))) {
    throw "Missing Linux scorer: $scoreBin"
}

docker run --rm `
    -v "${dockerRepo}:/work" `
    -w /work `
    $Image `
    bash -lc "chmod +x '$scoreBin' && ./'$scoreBin' --run '$Run' --findings '$Findings' --team '$Team' --out '$Out' && test -f '$Out' && cat '$Out'"
