param(
    [ValidateSet("x86", "x64", "auto")][string]$Architecture = "auto",
    [string]$PythonExe,
    [switch]$SkipInstaller
)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Invoke-Checked {
    param([string]$Program, [string[]]$Arguments)
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Falha ao executar $Program. Confira o erro acima." }
}
if ($env:OS -ne "Windows_NT") { throw "Compile os executaveis em um computador Windows." }
if ($Architecture -eq "auto") {
    foreach ($variant in @("x86", "x64")) {
        & $PSCommandPath -Architecture $variant -SkipInstaller
        if ($LASTEXITCODE -ne 0) { throw "Falha na compilacao $variant." }
    }
} else {
    $venvFolder = ".venv-$Architecture"
    $venvPython = Join-Path $PSScriptRoot "$venvFolder\Scripts\python.exe"
    if (-not (Test-Path $venvPython)) {
        if ($PythonExe) {
            Invoke-Checked $PythonExe @("-m", "venv", $venvFolder)
        } else {
            $pythonVersion = if ($Architecture -eq "x86") { "-3.10-32" } else { "-3.12-64" }
            Invoke-Checked "py" @($pythonVersion, "-m", "venv", $venvFolder)
        }
    }
    $actualBits = & $venvPython -c "import struct; print(struct.calcsize('P')*8)"
    $expectedBits = if ($Architecture -eq "x86") { 32 } else { 64 }
    if ([int]$actualBits -ne $expectedBits) { throw "O Python precisa ser de $expectedBits bits." }
    $requirements = if ($Architecture -eq "x86") { "requirements-build-x86.txt" } else { "requirements-build.txt" }
    Invoke-Checked $venvPython @("-m", "pip", "install", "-r", $requirements)
    $previousPlatform = $env:QT_QPA_PLATFORM
    $previousBinding = $env:POWER_ACADEMIA_QT_BINDING
    $previousArchitecture = $env:POWER_ACADEMIA_ARCH
    try {
        $env:QT_QPA_PLATFORM = "offscreen"
        $env:POWER_ACADEMIA_QT_BINDING = if ($Architecture -eq "x86") { "PySide2" } else { "PySide6" }
        $env:POWER_ACADEMIA_ARCH = $Architecture
        Invoke-Checked $venvPython @("-m", "unittest", "discover", "-s", "tests", "-v")
        Invoke-Checked $venvPython @("-m", "PyInstaller", "--noconfirm", "--clean", "--distpath", "dist\$Architecture", "--workpath", "build\$Architecture", "PowerAcademia.spec")
        & (Join-Path $PSScriptRoot "scripts\verify_binary.ps1") -Executable (Join-Path $PSScriptRoot "dist\$Architecture\PowerAcademia\PowerAcademia.exe") -Bits $expectedBits
    } finally {
        $env:QT_QPA_PLATFORM = $previousPlatform
        $env:POWER_ACADEMIA_QT_BINDING = $previousBinding
        $env:POWER_ACADEMIA_ARCH = $previousArchitecture
    }
}
if (-not $SkipInstaller) {
    $compiler = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    $compilerPath = if ($compiler) { $compiler.Source } else { "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe" }
    if (-not (Test-Path $compilerPath)) { throw "Instale Inno Setup 6 de 32 bits para gerar os instaladores." }
    $variants = if ($Architecture -eq "auto") { @("x86", "x64", "auto") } else { @($Architecture) }
    foreach ($variant in $variants) { Invoke-Checked $compilerPath @("/DBuildArchitecture=$variant", "installer.iss") }
    Write-Host "Instaladores gerados em output\." -ForegroundColor Green
}
