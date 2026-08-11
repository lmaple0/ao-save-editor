[CmdletBinding()]
param(
    [ValidateSet("OneFile", "OneDir")]
    [string]$Mode = "OneFile",

    [string]$PythonPath = ""
)

$ErrorActionPreference = "Stop"
$PackageRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$SpecPath = Join-Path $PSScriptRoot "ao_save_editor.spec"
$DistPath = Join-Path $PackageRoot "dist\windows"
$WorkPath = Join-Path $PackageRoot ("build\pyinstaller\" + $Mode.ToLowerInvariant())

if ($PythonPath) {
    if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) {
        throw "Python executable not found: $PythonPath"
    }
    $Launcher = $PythonPath
    $LauncherPrefix = @()
}
elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $Launcher = "py"
    $LauncherPrefix = @("-3.13")
}
elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $Launcher = "python"
    $LauncherPrefix = @()
}
else {
    throw "Python 3.13 was not found. Pass -PythonPath with an explicit python.exe path."
}

$PyInstallerArgs = @(
    "-m", "PyInstaller",
    "--noconfirm",
    "--clean",
    "--distpath", $DistPath,
    "--workpath", $WorkPath,
    $SpecPath
)

$PreviousMode = $env:AO_SAVE_EDITOR_BUILD_MODE
$env:AO_SAVE_EDITOR_BUILD_MODE = $Mode.ToLowerInvariant()
try {
    & $Launcher @LauncherPrefix @PyInstallerArgs
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller failed with exit code $LASTEXITCODE"
    }
}
finally {
    $env:AO_SAVE_EDITOR_BUILD_MODE = $PreviousMode
}

$Artifact = if ($Mode -eq "OneFile") {
    Join-Path $DistPath "AoSaveEditor.exe"
}
else {
    Join-Path $DistPath "AoSaveEditor\AoSaveEditor.exe"
}
if (-not (Test-Path -LiteralPath $Artifact -PathType Leaf)) {
    throw "Expected build artifact was not created: $Artifact"
}

$File = Get-Item -LiteralPath $Artifact
$Hash = (Get-FileHash -LiteralPath $Artifact -Algorithm SHA256).Hash
Write-Host ("Built {0}: {1:N2} MiB" -f $Mode, ($File.Length / 1MB))
Write-Host "Artifact: $($File.FullName)"
Write-Host "SHA-256: $Hash"
