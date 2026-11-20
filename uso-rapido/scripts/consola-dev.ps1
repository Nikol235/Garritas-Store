param(
  [Parameter(Mandatory)][ValidateSet('java','frontend','docker')][string]$Tipo,
  [Parameter(Mandatory)][string]$Nombre,
  [Parameter(Mandatory)][string]$Ruta,
  [Parameter(Mandatory)][string]$Log
)

$Host.UI.RawUI.WindowTitle = "Garritas DEV | $Nombre"
$ErrorActionPreference = 'Continue'
Write-Host "Garritas DEV | $Nombre"

switch ($Tipo) {
  'java' {
    $env:SPRING_PROFILES_ACTIVE = if ($Nombre -eq 'garritas-config') { 'native' } else { 'dev' }
    $env:LOG_PATH = Split-Path $Log -Parent
    $env:LOGGING_FILE_NAME = Join-Path $env:LOG_PATH 'application.log'
    $env:LOGGING_CONFIG = $null
    $env:JAVA_TOOL_OPTIONS = '-Xms64m -Xmx384m'
    $java = if ($env:JAVA_HOME) { Join-Path $env:JAVA_HOME 'bin/java.exe' } else { 'java.exe' }
    & $java -jar $Ruta 2>&1 | Tee-Object -FilePath $Log
  }
  'frontend' {
    $env:NG_CLI_ANALYTICS = 'false'
    & node.exe $Ruta serve --host 127.0.0.1 2>&1 | Tee-Object -FilePath $Log
  }
  'docker' {
    docker compose -f $Ruta logs --follow --tail 60 $Nombre 2>&1 | Tee-Object -FilePath $Log
  }
}

exit $LASTEXITCODE
