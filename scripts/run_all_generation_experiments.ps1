param(
    [string[]]$Tasks = @("T1", "T2", "T3"),
    [string]$Model = "qwen2.5-coder:1.5b",
    [string]$BaseUrl = "http://localhost:11434",
    [int]$BatchSize = 50,
    [double]$Temperature = 0.2,
    [double]$Tolerance = 0.10,
    [int]$Repetitions = 1,
    [int]$MaxIterations = 3,
    [int]$MaxRepairAttempts = 2,
    [string[]]$Conditions = @(
        "non_adaptive_baseline",
        "task_aware_non_adaptive",
        "task_aware_iterative"
    ),
    [Alias("h", "?")]
    [switch]$Help,
    [switch]$StopOnError
)

$ErrorActionPreference = "Stop"

if ($Help) {
    Write-Output @"
Usage:
  pwsh -File .\scripts\run_all_generation_experiments.ps1 [options]

Options:
  -Tasks T1,T2,T3
  -Model qwen2.5-coder:1.5b
  -BaseUrl http://localhost:11434
  -BatchSize 100
  -Temperature 0.2
  -Tolerance 0.10
  -Repetitions 3
  -MaxIterations 3
  -MaxRepairAttempts 2
  -Conditions non_adaptive_baseline,task_aware_non_adaptive,task_aware_iterative
  -StopOnError
"@
    exit 0
}

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
        "--base-url" $BaseUrl `
        "--batch-size" $BatchSize `
        "--temperature" $Temperature `
        "--tolerance" $Tolerance `
        "--repetitions" $Repetitions `
        "--max-iterations" $MaxIterations `
        "--max-repair-attempts" $MaxRepairAttempts `
        "--conditions" $Conditions

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
