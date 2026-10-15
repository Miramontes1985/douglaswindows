param([Parameter(Mandatory=$true)][string]$Executable, [Parameter(Mandatory=$true)][int]$Bits)
$ErrorActionPreference = "Stop"
$reportPath = Join-Path $env:TEMP ("power-academia-" + [guid]::NewGuid().ToString() + ".json")
$process = Start-Process -FilePath $Executable -ArgumentList @("--self-test", ('"' + $reportPath + '"')) -PassThru
try {
    if (-not $process.WaitForExit(60000)) {
        $process.Kill()
        throw "O aplicativo nao concluiu a verificacao em 60 segundos."
    }
    if ($process.ExitCode -ne 0 -or -not (Test-Path $reportPath)) {
        throw "O executavel falhou ao abrir. Codigo: $($process.ExitCode)."
    }
    $report = Get-Content $reportPath -Raw | ConvertFrom-Json
    $report | ConvertTo-Json
    if (-not $report.ok -or $report.architecture -ne $Bits -or -not $report.frozen) {
        throw "Falha na verificacao do pacote."
    }
} finally {
    Remove-Item $reportPath -ErrorAction SilentlyContinue
}
