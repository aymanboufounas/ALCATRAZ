param(
    [string]$UnityEditor = "C:\Program Files\Unity\Hub\Editor\6000.0.62f1\Editor\Unity.exe",
    [switch]$RequireMinimumSize,
    [string]$PythonExecutable = "python"
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $UnityEditor)) { throw 'Pass -UnityEditor with your Unity.exe path.' }
$ProjectDirectory = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$ReportDirectory = Join-Path $ProjectDirectory 'Builds\Reports'
New-Item -ItemType Directory -Force -Path $ReportDirectory | Out-Null
$BuildLog = Join-Path $ReportDirectory 'AlcatrazWindowsBuild.log'
& $UnityEditor -batchmode -quit -projectPath $ProjectDirectory -buildTarget Win64 `
    -executeMethod Blackstone.Alcatraz.Editor.AlcatrazPreparation.Build -logFile $BuildLog
if ($LASTEXITCODE -ne 0) { throw "Build failed. Read $BuildLog" }
Write-Host (Join-Path $ProjectDirectory 'Builds\Windows\AlcatrazEscape.exe')
Write-Host (Join-Path $ReportDirectory 'LatestPlayerBuild.json')
if ($RequireMinimumSize) {
    $Verifier = Join-Path $ProjectDirectory 'Tools\verify_player_build.py'
    $PlayerDirectory = Join-Path $ProjectDirectory 'Builds\Windows'
    & $PythonExecutable $Verifier $PlayerDirectory --require-minimum 5000000000 --require-clean-source
    if ($LASTEXITCODE -ne 0) { throw 'The player was built, but its export integrity or 5 GB size qualification failed.' }
}
