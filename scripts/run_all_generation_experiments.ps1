param(
    [string[]]$Tasks = @("T1", "T2", "T3"),
    [string]$Model = "qwen2.5-coder:1.5b",
    [int]$BatchSize = 50,
    [int]$Repetitions = 1,
    [int]$MaxIterations = 3,
    [int]$MaxRepairAttempts = 2,
    [switch]$StopOnError
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (Test-Path -LiteralPath $VenvPython) {
    $Python = $VenvPython
} else {
    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $PythonCommand) {
        throw "Python was not found. Activate the virtual environment or install Python."
    }
    $Python = $PythonCommand.Source
}

Set-Location -LiteralPath $ProjectRoot
$Failures = 0

foreach ($Task in $Tasks) {
    Write-Host "Starting generation experiment for $Task" -ForegroundColor Cyan

    & $Python "scripts/run_generation_experiment.py" `
        "--task" $Task `
        "--model" $Model `
        "--batch-size" $BatchSize `
        "--repetitions" $Repetitions `
        "--max-iterations" $MaxIterations `
        "--max-repair-attempts" $MaxRepairAttempts

    if ($LASTEXITCODE -ne 0) {
        $Failures++
        Write-Warning "$Task failed with exit code $LASTEXITCODE."
        if ($StopOnError) {
            throw "$Task failed; stopping because -StopOnError was specified."
        }
    } else {
        Write-Host "Completed generation experiment for $Task" -ForegroundColor Green
    }
}

if ($Failures -gt 0) {
    Write-Warning "$Failures experiment(s) failed."
    exit 1
}

Write-Host "All generation experiments completed successfully." -ForegroundColor Green
