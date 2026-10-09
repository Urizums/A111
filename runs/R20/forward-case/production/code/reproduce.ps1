param(
    [Parameter(Mandatory=$true)][string]$Inputs,
    [Parameter(Mandatory=$true)][string]$OutputRoot
)
$ErrorActionPreference = 'Stop'
$taskCode = $PSScriptRoot
if (Test-Path -LiteralPath $OutputRoot) { throw 'OutputRoot must be absent; preserve earlier runs.' }
New-Item -ItemType Directory -Path $OutputRoot | Out-Null
& python -X utf8 -B (Join-Path $taskCode 'calibrate.py') --inputs $Inputs --out (Join-Path $OutputRoot 'results')
if ($LASTEXITCODE -ne 0) { throw "Production failed: $LASTEXITCODE" }
& python -X utf8 -B (Join-Path $taskCode 'author_check.py') --inputs $Inputs --outputs (Join-Path $OutputRoot 'results') --report (Join-Path $OutputRoot 'author-check.json')
if ($LASTEXITCODE -ne 0) { throw "Receiving check failed: $LASTEXITCODE" }
& python -X utf8 -B (Join-Path $taskCode 'calibrate.py') --inputs $Inputs --out (Join-Path $OutputRoot 'second-run')
if ($LASTEXITCODE -ne 0) { throw "Rerun failed: $LASTEXITCODE" }
& python -X utf8 -B (Join-Path $taskCode 'compare_rerun.py') --first (Join-Path $OutputRoot 'results') --second (Join-Path $OutputRoot 'second-run') --report (Join-Path $OutputRoot 'reproduction.json')
if ($LASTEXITCODE -ne 0) { throw "Comparison failed: $LASTEXITCODE" }
