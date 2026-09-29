# Prueba de humo del arranque del exe congelado (BLD-020).
#
# Arranca el ejecutable con GUARDIAS_PRUEBA_DE_ARRANQUE, espera a que termine
# con un tiempo limite y comprueba en su registro que ha llegado al login (o a
# la ventana principal). Pase lo que pase, deja a la vista el final del registro,
# faulthandler.log y los errores del Visor de eventos, que es lo que hace falta
# para saber por que se ha ido.
#
# Uso: pwsh scripts/prueba_arranque_windows.ps1 -Exe dist/GuardiasDePatio/GuardiasDePatio.exe
#
# Solo ASCII a proposito: asi da igual con que PowerShell se abra.

param(
    [Parameter(Mandatory = $true)][string]$Exe,
    [ValidateSet("login", "ventana")][string]$Modo = "ventana",
    [int]$Segundos = 240,
    [string]$Copia = ""
)

$ErrorActionPreference = "Stop"
$Datos = Join-Path $env:APPDATA "GuardiasDePatio"
$Logs = Join-Path $Datos "logs"
$Marca = if ($Modo -eq "login") { "PRUEBA DE ARRANQUE: login a la vista" } else { "PRUEBA DE ARRANQUE: ventana principal a la vista" }

if (-not (Test-Path $Exe)) { Write-Host "[ERROR] No existe $Exe"; exit 1 }
$Exe = (Resolve-Path $Exe).Path
Write-Host "[INFO] Ejecutable: $Exe"
Write-Host "[INFO] Modo: $Modo, limite $Segundos s"

$antes = @()
if (Test-Path $Logs) { $antes = Get-ChildItem $Logs -Filter "app_*.log" | ForEach-Object { $_.FullName } }
$inicio = Get-Date

$env:GUARDIAS_PRUEBA_DE_ARRANQUE = $Modo
$proceso = Start-Process -FilePath $Exe -WorkingDirectory (Split-Path $Exe) -PassThru
$termino = $proceso.WaitForExit($Segundos * 1000)
Remove-Item Env:GUARDIAS_PRUEBA_DE_ARRANQUE -ErrorAction SilentlyContinue

$codigo = $null
if (-not $termino) {
    Write-Host "[ERROR] Sigue abierto tras $Segundos s: se da por colgado y se cierra"
    Stop-Process -Id $proceso.Id -Force -ErrorAction SilentlyContinue
} else {
    $codigo = $proceso.ExitCode
    Write-Host "[INFO] Ha salido con codigo $codigo en $([int]((Get-Date) - $inicio).TotalSeconds) s"
}

$registro = $null
if (Test-Path $Logs) {
    $registro = Get-ChildItem $Logs -Filter "app_*.log" |
        Where-Object { $antes -notcontains $_.FullName } |
        Sort-Object LastWriteTime | Select-Object -Last 1
}

$llego = $false
if ($null -eq $registro) {
    Write-Host "[ERROR] No se ha creado ningun app_*.log: el proceso no llego a ejecutar Python"
} else {
    Write-Host "`n=== $($registro.Name): lo que no es DEBUG, ultimas 150 lineas ==="
    Get-Content $registro.FullName -Encoding UTF8 |
        Where-Object { $_ -notmatch " - DEBUG - " } |
        Select-Object -Last 150 | ForEach-Object { Write-Host $_ }
    $llego = [bool](Select-String -Path $registro.FullName -SimpleMatch $Marca -Quiet)
}

$falta = Join-Path $Logs "faulthandler.log"
if ((Test-Path $falta) -and ((Get-Item $falta).Length -gt 0)) {
    Write-Host "`n=== faulthandler.log ==="
    Get-Content $falta | Select-Object -Last 80 | ForEach-Object { Write-Host $_ }
}

Write-Host "`n=== Visor de eventos (Aplicacion, errores desde el arranque) ==="
try {
    Get-WinEvent -FilterHashtable @{ LogName = "Application"; Level = 1, 2; StartTime = $inicio } -ErrorAction Stop |
        Select-Object -First 10 | ForEach-Object { Write-Host "$($_.TimeCreated) $($_.ProviderName) $($_.Id)`n$($_.Message)`n" }
} catch {
    Write-Host "(sin errores)"
}

if ($Copia) {
    New-Item -ItemType Directory -Force -Path $Copia | Out-Null
    if (Test-Path $Logs) { Copy-Item -Path (Join-Path $Logs "*") -Destination $Copia -Force }
}

if ($llego -and $termino -and $codigo -eq 0) {
    Write-Host "`n[OK] $Marca y salida limpia"
    exit 0
}
Write-Host "`n[ERROR] El exe no ha llegado a: $Marca (termino=$termino, codigo=$codigo)"
exit 1
