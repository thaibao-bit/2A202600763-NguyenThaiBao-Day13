# Run scorer in Docker

Use this when the Windows `observathon-score.exe` is broken but the Linux
`bin/practice/observathon-score` binary exists.

From the project root:

```powershell
.\harness\score_docker.ps1
```

Equivalent raw Docker command:

```powershell
$repo = (Get-Location).Path -replace "\\", "/"
docker run --rm -v "${repo}:/work" -w /work ubuntu:24.04 bash -lc "chmod +x bin/practice/observathon-score && ./bin/practice/observathon-score --run run_output.json --findings solution/findings.json --team NguyenThaiBao --out score.json && cat score.json"
```

Make sure `run_output.json` already exists before running the scorer.

If the Windows simulator also fails with a PyInstaller Python DLL error, run the
Linux simulator in Docker:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\harness\sim_docker.ps1 `
  -Phase practice `
  -Questions harness/public_questions.json `
  -Out run_output_public_questions.json
```

When `bin/public` or `bin/private` is available, pass `-Phase public` or
`-Phase private` to both scripts so the signed phase matches the scorer.
