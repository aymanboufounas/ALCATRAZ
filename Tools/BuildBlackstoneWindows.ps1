param([string]$UnityEditor = "C:\Program Files\Unity\Hub\Editor\6000.0.62f1\Editor\Unity.exe")
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $UnityEditor)) { throw 'Pass -UnityEditor with your Unity.exe path.' }
$ProjectDirectory = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$BuildLog = Join-Path $ProjectDirectory 'Validation\BlackstoneWindowsBuild.log'
& $UnityEditor -batchmode -quit -projectPath $ProjectDirectory -buildTarget Win64 `
    -executeMethod Blackstone.Editor.BlackstoneProjectTools.BuildWindows -logFile $BuildLog
if ($LASTEXITCODE -ne 0) { throw "Build failed. Read $BuildLog" }
Write-Host (Join-Path $ProjectDirectory 'Builds\Windows\BlackstoneIsland.exe')
