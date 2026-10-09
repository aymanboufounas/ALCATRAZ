param(
    [string]$UnityEditor = "C:\Program Files\Unity\Hub\Editor\6000.0.62f1\Editor\Unity.exe"
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $UnityEditor)) {
    throw 'Unity Editor was not found. Pass -UnityEditor with the full path to your Unity 6.0 LTS Unity.exe.'
}
$ProjectDirectory = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$BuildLog = Join-Path $ProjectDirectory 'Validation\WindowsBuild.log'
& $UnityEditor -batchmode -quit -projectPath $ProjectDirectory -buildTarget Win64 `
    -executeMethod DesertShift.Editor.ProjectTools.BuildWindows -logFile $BuildLog
if ($LASTEXITCODE -ne 0) { throw "Unity build failed. Read $BuildLog" }
Write-Host (Join-Path $ProjectDirectory 'Builds\Windows\DesertShift.exe')
