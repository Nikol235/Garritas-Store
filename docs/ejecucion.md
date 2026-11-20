# Ejecución y diagnóstico

## Separación como en Pagatu

Kafka y Kafka UI están en `kafka/compose-dev.yml`; Keycloak y su base en `keycloak/compose-dev.yml`. Cada microservicio conserva su `compose-dev.yml` para PostgreSQL y su Maven Wrapper. `infra/` contiene Config Server, Eureka y Gateway. Las automatizaciones y el agregador Maven se ubican en `uso-rapido/`.

## Arranque manual en DEV con PowerShell

En Windows, enciende Docker Desktop y verifica que JDK 21 y Node 24 estén en PATH. Para la sustentación abre **un PowerShell por aplicación** y deja cada ventana abierta. Cada bloque de abajo parte de la raíz del repositorio en una ventana nueva. Este recorrido usa los Maven Wrapper, los Compose DEV y el servidor local de Angular.

### 0. Instalar la librería compartida

Ejecuta una vez desde la raíz. Repite si modificas `infra/garritas-common`.

```powershell
.\infra\garritas-config\mvnw.cmd -f infra/garritas-common/pom.xml -B install -DskipTests
```

### 1. Infraestructura

Abre tres ventanas en este orden. Config Server debe estar listo antes de arrancar Eureka y Gateway.

```powershell
cd infra/garritas-config
.\mvnw.cmd spring-boot:run '-Dspring-boot.run.profiles=native'
```

```powershell
cd infra/garritas-eureka
.\mvnw.cmd spring-boot:run '-Dspring-boot.run.profiles=dev'
```

```powershell
cd infra/garritas-gateway
.\mvnw.cmd spring-boot:run '-Dspring-boot.run.profiles=dev'
```

Abre Eureka en `http://localhost:18761`. Gateway escucha en el puerto `18080`. Las rutas de negocio estarán disponibles cuando arranquen y se registren sus microservicios.

### 2. Kafka y Keycloak

Abre una ventana para Kafka y otra para Keycloak. Espera a que estén listos antes de iniciar los microservicios.

```powershell
cd kafka
docker compose -f compose-dev.yml up -d --wait --wait-timeout 240
```

```powershell
cd keycloak
docker compose -f compose-dev.yml up -d --wait --wait-timeout 240
```

Kafka UI está en `http://localhost:18085`. Comprueba que el clúster `garritas` esté conectado. El realm de Keycloak responde en `http://localhost:18180/realms/garritas/.well-known/openid-configuration`.

### 3. Microservicios de negocio

Usa ocho ventanas, una por bloque. En cada una espera que Docker arranque la base antes de ejecutar Maven. Empieza por Catálogo e inicia Pago después de Kafka.

**Catálogo**

```powershell
cd services/garritas-catalogo-ms
docker compose -f compose-dev.yml up -d --wait --wait-timeout 120
.\mvnw.cmd spring-boot:run '-Dspring-boot.run.profiles=dev'
```

**Institución**

```powershell
cd services/garritas-institucion-ms
docker compose -f compose-dev.yml up -d --wait --wait-timeout 120
.\mvnw.cmd spring-boot:run '-Dspring-boot.run.profiles=dev'
```

**Usuario**

```powershell
cd services/garritas-usuario-ms
docker compose -f compose-dev.yml up -d --wait --wait-timeout 120
.\mvnw.cmd spring-boot:run '-Dspring-boot.run.profiles=dev'
```

**Bienestar**

```powershell
cd services/garritas-bienestar-ms
docker compose -f compose-dev.yml up -d --wait --wait-timeout 120
.\mvnw.cmd spring-boot:run '-Dspring-boot.run.profiles=dev'
```

**Venta**

```powershell
cd services/garritas-venta-ms
docker compose -f compose-dev.yml up -d --wait --wait-timeout 120
.\mvnw.cmd spring-boot:run '-Dspring-boot.run.profiles=dev'
```

**Pago**

```powershell
cd services/garritas-pago-ms
docker compose -f compose-dev.yml up -d --wait --wait-timeout 120
.\mvnw.cmd spring-boot:run '-Dspring-boot.run.profiles=dev'
```

**Envío**

```powershell
cd services/garritas-envio-ms
docker compose -f compose-dev.yml up -d --wait --wait-timeout 120
.\mvnw.cmd spring-boot:run '-Dspring-boot.run.profiles=dev'
```

**Citas**

```powershell
cd services/garritas-citas-ms
docker compose -f compose-dev.yml up -d --wait --wait-timeout 120
.\mvnw.cmd spring-boot:run '-Dspring-boot.run.profiles=dev'
```

### 4. Angular y verificación

En otra ventana:

```powershell
cd clients/garritas-frontend
npm.cmd ci
npm.cmd start
```

Abre la tienda en `http://localhost:4200` y verifica en Eureka que se registren los microservicios. Desde un PowerShell de comprobación consulta por Gateway:

```powershell
Invoke-RestMethod -Method Get -Uri 'http://localhost:18080/api/v1/productos'
```

### 5. Grafana y demostración de caída

Para la sustentación, abre una ventana más y levanta observabilidad después de Keycloak.

```powershell
cd obs
docker compose -f compose-dev.yml up -d
```

Si ya tenías el Compose de observabilidad en marcha antes de actualizar el repositorio, ejecuta también `docker compose -f compose-dev.yml restart garritas-prometheus garritas-grafana` desde `obs` para cargar la configuración nueva.

Abre `http://localhost:13000/d/garritas-infra` y entra con el usuario local `admin` y contraseña `local-grafana`, salvo que hayas configurado otra. En **Garritas - Infraestructura**, el panel **Estado de las aplicaciones** consulta las métricas de cada aplicación Spring. Usa **ARRIBA** si Prometheus recibe las métricas y **CAÍDO** si deja de recibirlas. El estado se consulta cada cinco segundos y Grafana refresca cada diez.

1. Comprueba que Catálogo esté **ARRIBA** y que la consulta a Gateway responda.
2. Pulsa **Ctrl+C** en el PowerShell de Catálogo. Deja su PostgreSQL en marcha. Espera el refresco de Grafana y comprueba que la tarjeta siga visible como **CAÍDO**. Repite la consulta a Gateway para ver el fallo de la ruta.
3. En esa misma ventana, ejecuta otra vez `.\mvnw.cmd spring-boot:run '-Dspring-boot.run.profiles=dev'`. Comprueba que Catálogo vuelva a **ARRIBA**, se registre en Eureka y la consulta a Gateway responda de nuevo.

### 6. Detener la demo

Usa **Ctrl+C** en cada PowerShell de Java y Angular. Para bajar solo los contenedores de una carpeta, desde esa carpeta ejecuta `docker compose -f compose-dev.yml down`. Para conservar también los contenedores creados, usa `docker compose -f compose-dev.yml stop`. Si vas a detener Keycloak, baja primero el Compose de observabilidad. Así puedes detener únicamente lo que pertenece a la demo.

## Puertos de negocio DEV

| Servicio | Aplicación | PostgreSQL |
|---|---|---|
| Venta | 8081 | 15441 |
| Institución | 8082 | 15442 |
| Envío | 8083 | 15443 |
| Citas | 8084 | 15444 |
| Catálogo | 8085 | 15445 |
| Usuario | 8086 | 15446 |
| Pago | 8087 | 15447 |
| Bienestar | 8088 | 15448 |

## Operación

- `bash uso-rapido/scripts/dev.sh status --observability` comprueba endpoints y conexión Kafka. No considera un PID como prueba suficiente de funcionamiento.
- Los procesos y logs gestionados están en `.runtime/`; cada JVM ejecuta una copia de su JAR para que una compilación posterior no modifique un archivo en uso.
- Después de cambiar Java: `build`, `stop`, `all`. No ejecutes dos compilaciones Maven sobre las mismas carpetas al mismo tiempo.
- `stop` detiene los procesos gestionados; `down` baja además los contenedores y conserva los volúmenes. No eliminar volúmenes para solucionar un error de arranque sin preservar los datos.
- Si 4200 ya sirve Garritas, se conserva ese proceso existente. El lanzador no intenta apropiarse de otro servidor; para actualizarlo, detén su terminal original.
- En la nube se puede indicar `MAVEN_SETTINGS` para el proxy y `MAVEN_USER_HOME` para una caché escribible. Nunca desactivar TLS ni firmas para descargar dependencias.
- La monitorización prepara permisos de archivos públicos de `obs/` y comunica los contenedores por sus nombres internos, sin pasar por el proxy externo.

## Roles y datos

Las sedes tienen baja lógica: desactivarlas impide nuevas selecciones sin borrar el historial de pedidos. Las citas verifican que la mascota pertenezca al cliente y que la sede/profesional estén activos. La clave única de profesional y hora evita reservas concurrentes para el mismo bloque. No se permiten confirmar citas canceladas ni atender citas sin confirmar.

Los envíos se crean solo para ventas pagadas y pertenecen al mismo cliente de la venta; hay un envío por pedido. Solo ADMIN puede marcar tránsito/entrega. Un cliente no puede cancelar un envío en tránsito o ya entregado.

Una especialidad utilizada no se elimina: primero se desasigna de sus profesionales. Cambiar las asociaciones se confirma en una única transacción de la base de Bienestar.

## Actualización académica y recuperación de arranque

[Asignación y migraciones](asignacion-y-sustentacion.md) explica el traslado de despachos a Venta, las nuevas relaciones y las edades en días/meses. Los puertos no cambian. `build` utiliza `clean package` para evitar que un JAR conserve una copia anterior de la librería común.

En Windows puedes leer los logs en las consolas visibles y en `.runtime`. No ejecutes dos arranques simultáneamente ni alternes copias en C: y D: que comparten puertos y contenedores. `-Accion detener` comprueba el identificador y la hora de inicio de cada consola antes de detenerla junto con sus procesos hijos. Los contenedores y volúmenes se conservan. Un registro sin procesos vivos se retira al iniciar.

Swagger de cada servicio está en `http://localhost:PUERTO/swagger-ui/index.html`; la documentación es consultable y las operaciones protegidas requieren un JWT Bearer mediante Authorize. No se incluyen tokens en esta documentación.
