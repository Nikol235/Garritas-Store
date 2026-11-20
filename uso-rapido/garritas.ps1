param([ValidateSet('build','iniciar','estado','detener','test')][string]$Accion='iniciar')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$runtime=Join-Path $root '.runtime'
New-Item -ItemType Directory -Force $runtime | Out-Null
$pidFile=Join-Path $runtime 'windows-processes.json'
$wrapper=Join-Path $root 'infra/garritas-config/mvnw.cmd'
$pom=Join-Path $root 'uso-rapido/pom.xml'
Set-Location $root

function Invoke-Checked([scriptblock]$Command) {
  & $Command
  if($LASTEXITCODE -ne 0){throw "Falló un comando (salida $LASTEXITCODE). Revisa el mensaje anterior."}
}
function Wait-Ready([string]$Url, $Process) {
  for($i=0;$i -lt 120;$i++){
    if($Process -and $Process.HasExited){throw "La consola que iniciaba $Url terminó. Revisa los logs de .runtime."}
    try {$r=Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 3;if($r.StatusCode -eq 200){return}} catch {}
    Start-Sleep -Seconds 1
  }
  throw "No responde $Url. Revisa los logs de .runtime."
}
function Open-DevConsole([string]$Tipo, [string]$Nombre, [string]$Ruta, [string]$Log, [string]$Directorio) {
  $script=Join-Path $PSScriptRoot 'scripts/consola-dev.ps1'
  $process=Start-Process -FilePath 'powershell.exe' -WindowStyle Normal -WorkingDirectory $Directorio -PassThru -ArgumentList @(
    '-NoLogo','-NoProfile','-ExecutionPolicy','RemoteSigned','-File',"`"$script`"",
    '-Tipo',$Tipo,'-Nombre',"`"$Nombre`"",'-Ruta',"`"$Ruta`"",'-Log',"`"$Log`""
  )
  $records.Add(@{id=$process.Id;started=$process.StartTime.ToUniversalTime().ToString('o')})
  ConvertTo-Json -InputObject @($records.ToArray()) | Set-Content $pidFile
  $process
}
function Start-DevCompose([string]$Compose, [switch]$Wait) {
  $argsUp=@('compose','-f',$Compose,'up','-d')
  if($Wait){$argsUp+=@('--wait','--wait-timeout','240')}
  Invoke-Checked {docker @argsUp}
  $services=@(docker compose -f $Compose config --services)
  if($LASTEXITCODE -ne 0){throw "No se pudo leer $Compose."}
  $directory=Split-Path $Compose -Parent
  $project=Split-Path $directory -Leaf
  foreach($service in $services){
    $log=Join-Path $runtime "$project-$service-docker.log"
    Open-DevConsole 'docker' $service $Compose $log $directory | Out-Null
  }
}
$ports=[ordered]@{'garritas-config'=18888;'garritas-eureka'=18761;'garritas-catalogo-ms'=8085;'garritas-institucion-ms'=8082;'garritas-usuario-ms'=8086;'garritas-bienestar-ms'=8088;'garritas-venta-ms'=8081;'garritas-pago-ms'=8087;'garritas-envio-ms'=8083;'garritas-citas-ms'=8084;'garritas-gateway'=18080}
switch($Accion){
  'build' {
    Invoke-Checked {& $wrapper -f $pom -B -pl ':garritas-distributed' -am install -DskipTests}
    Invoke-Checked {& $wrapper -f $pom -B clean package -DskipTests}
    Push-Location (Join-Path $root 'clients/garritas-frontend')
    try {Invoke-Checked {npm.cmd ci};Invoke-Checked {npm.cmd run build}} finally {Pop-Location}
  }
  'test' {
    Invoke-Checked {& $wrapper -f $pom -B verify '-Deureka.client.register-with-eureka=false' '-Deureka.client.fetch-registry=false' '-Dspring.kafka.listener.auto-startup=false'}
  }
  'iniciar' {
    if(Test-Path $pidFile){
      $alive=@(Get-Content $pidFile -Raw | ConvertFrom-Json | ForEach-Object {
        $process=Get-Process -Id $_.id -ErrorAction SilentlyContinue
        if($process -and $process.StartTime.ToUniversalTime() -eq ([datetime]$_.started).ToUniversalTime()){$process}
      })
      if($alive.Count -gt 0){throw 'Hay procesos de este arranque todavía activos. Usa -Accion estado; para reiniciar, -Accion detener primero. No ejecutes iniciar dos veces.'}
      Remove-Item $pidFile
      Write-Host 'Se retiró un registro de procesos ya finalizados. Se iniciará una sesión nueva.'
    }
    $modules=@{}
    foreach($name in $ports.Keys){
      $module=Join-Path $root "services/$name"
      if(!(Test-Path $module)){$module=Join-Path $root "infra/$name"}
      $jar=Join-Path $module "target/$name-0.0.1-SNAPSHOT.jar"
      if(!(Test-Path $jar)){throw "Falta $jar. Ejecuta primero -Accion build."}
      $modules[$name]=@{directory=$module;jar=$jar}
    }
    $records=[System.Collections.Generic.List[object]]::new()
    Start-DevCompose (Join-Path $root 'kafka/compose-dev.yml') -Wait
    Start-DevCompose (Join-Path $root 'keycloak/compose-dev.yml') -Wait
    Get-ChildItem (Join-Path $root 'services') -Directory | ForEach-Object {
      $compose=Join-Path $_.FullName 'compose-dev.yml'
      if(Test-Path $compose){Start-DevCompose $compose}
    }
    foreach($entry in $ports.GetEnumerator()){
      $name=$entry.Key
      $module=$modules[$name]
      $logs=Join-Path $runtime $name
      New-Item -ItemType Directory -Force $logs | Out-Null
      $copy=Join-Path $logs 'app.jar'
      Copy-Item -Force $module.jar $copy
      $process=Open-DevConsole 'java' $name $copy (Join-Path $logs 'console.log') $module.directory
      Wait-Ready "http://localhost:$($entry.Value)/actuator/health/readiness" $process
      Write-Host "$name disponible"
    }
    Wait-Ready 'http://localhost:18080/api/v1/productos'
    & (Join-Path $PSScriptRoot 'scripts/migrar-despachos.ps1')
    $frontend=Join-Path $root 'clients/garritas-frontend'
    if(!(Test-Path (Join-Path $frontend 'node_modules'))){Push-Location $frontend;try{Invoke-Checked {npm.cmd ci}}finally{Pop-Location}}
    $cli=Join-Path $frontend 'node_modules/@angular/cli/bin/ng.js'
    $process=Open-DevConsole 'frontend' 'Angular' $cli (Join-Path $runtime 'frontend.log') $frontend
    Wait-Ready 'http://localhost:4200' $process
    Write-Host 'Garritas iniciado. Ejecuta -Accion estado para comprobar los puertos.'
  }
  'estado' {
    foreach($entry in $ports.GetEnumerator()){
      try{$r=Invoke-WebRequest -UseBasicParsing -Uri "http://localhost:$($entry.Value)/actuator/health/readiness" -TimeoutSec 3;Write-Host "OK $($entry.Key)"}catch{Write-Host "FALLO $($entry.Key)"}
    }
    foreach($port in @(4200,18085,18180)){
      try{Invoke-WebRequest -UseBasicParsing -Uri "http://localhost:$port/" -TimeoutSec 3 | Out-Null;Write-Host "OK puerto $port"}catch{Write-Host "FALLO puerto $port"}
    }
  }
  'detener' {
    if(Test-Path $pidFile){
      $records=@(Get-Content $pidFile -Raw | ConvertFrom-Json)
      foreach($record in $records){
        $process=Get-Process -Id $record.id -ErrorAction SilentlyContinue
        if($process -and $process.StartTime.ToUniversalTime() -eq ([datetime]$record.started).ToUniversalTime()){
          Invoke-Checked {taskkill.exe /PID $process.Id /T /F}
        }
      }
      Remove-Item $pidFile
    }
    Write-Host 'Consolas DEV detenidas. Los contenedores y volúmenes se conservan.'
  }
}
