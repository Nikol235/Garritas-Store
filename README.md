# Garritas Store

Repositorio de continuidad para preparar el despliegue del proyecto. Conserva el historial de [Garritas-](https://github.com/Nikol235/Garritas-/tree/feat/garritas-store) hasta la versión `8944d5a`, incluidas Ventas por rol, fotos locales y constancias PDF. La rama principal de este repositorio es **main**.

**Estado:** ejecución local verificada; despliegue en Railway/Supabase por preparar. Los pagos de demostración se simulan por defecto. Checkout Pro requiere habilitación explícita y credenciales configuradas fuera del repositorio. Los manuales históricos mantienen enlaces a los commits originales como referencia; los comandos de clonación actuales son los siguientes.

Campus Juliaca · Sistemas Distribuidos · semestre 2026-2 · Grupo 2 · Ciclo 5 G · Sección única. [Descripción y temas del repositorio](docs/configuracion-del-repositorio.md).

## Clonar este repositorio

```powershell
git clone https://github.com/Nikol235/Garritas-Store.git
cd Garritas-Store
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force
$env:NG_CLI_ANALYTICS = "false"
```

[Descargar la guía de arranque manual en DEV (PDF)](docs/manuales/compartir/Garritas-Store-inicio-una-hoja.pdf) · [Comandos copiables en texto](docs/manuales/compartir/Garritas-Store-inicio-una-hoja.txt).

Clonar no copia bases de datos ni las fotos locales: su persistencia y respaldo se explican en la [guía de imágenes y comprobantes](docs/ventas-imagenes-y-comprobantes.md).

Tienda y bienestar para mascotas en el Perú. Microservicios con **Java 21 / Spring Boot 4**, PostgreSQL/Flyway, Config Server, Eureka, Gateway, Kafka, Keycloak y un cliente **Angular 22**.

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

#### Mercado Pago de prueba en DEV

Para probar Checkout Pro, usa el **Access Token de prueba** de una aplicación Checkout Pro de Mercado Pago Perú. En el mismo PowerShell de **Pago**, después de arrancar PostgreSQL y antes de iniciar Maven, ejecuta:

```powershell
$env:MP_CHECKOUT_ENABLED = 'true'
$env:MP_ACCESS_TOKEN = ([System.Net.NetworkCredential]::new('', (Read-Host 'Access Token de prueba' -AsSecureString))).Password
.\mvnw.cmd spring-boot:run '-Dspring-boot.run.profiles=dev'
```

Si Pago ya está corriendo, detenlo con **Ctrl+C** en su ventana antes de ejecutar el bloque. DEV usa enlaces de prueba y valida que los pagos correspondan a ese entorno. Si inicias sin habilitar Checkout Pro, el laboratorio usa la simulación interna.

Crea un pedido nuevo y abre **Mis compras → detalle → Consultar pago → Pagar con Mercado Pago**. Usa el comprador y los datos de tarjeta de prueba que te indica Mercado Pago. Cuando termines en el checkout, vuelve a la pestaña de Garritas en `http://localhost:4200` y pulsa **Verificar pago**. Comprueba una aprobación y un rechazo en pedidos distintos. La verificación consulta el proveedor aunque el checkout se haya abierto desde localhost. Mantén el token en tu PowerShell y fuera de Git.

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

## Estructura

```text
Garritas-Store/
├── .github/          # CI: compilación Java y pruebas/build de Angular
├── clients/          # garritas-frontend
├── docs/             # Arquitectura, ejecución y evidencia de validación
├── infra/            # Config Server, Eureka, Gateway y soporte técnico común
├── kafka/            # Broker Kafka y Kafka UI
├── keycloak/         # Keycloak, su PostgreSQL y el realm de demostración
├── obs/              # Prometheus, Loki, Promtail y Grafana
├── overrides/        # Personalización del sitio de documentación
├── services/         # Ocho microservicios de negocio, cada uno con PostgreSQL propio
└── uso-rapido/       # Ejemplo Python Kafka, arranque, pruebas y Compose integrado opcional
```

Los Compose y Dockerfiles de integración que estaban en la raíz se movieron a `uso-rapido/docker/`. Las herramientas están en `uso-rapido/scripts/`; el soporte común está en `infra/garritas-common/`. Las rutas de compilación y ejecución ya usan esta organización.

## Qué se puede hacer en Angular

| Pantalla | Cliente | Administrador |
|---|---|---|
| Catálogo, nueva orden y carrito | Buscar, filtrar, seleccionar sede y comprar | Gestionar productos y categorías; no comprar |
| Sedes | Consultar sedes activas del Perú y seleccionar una | Crear, editar, activar y desactivar sedes |
| Especialistas | Consultar profesionales y sus especialidades; reservar cita | Gestionar profesionales y asignar varias especialidades |
| Mi cuenta y mascotas | Editar su perfil y gestionar sus propias mascotas | Perfil propio y administración de clientes |
| Citas | Reservar una o varias prestaciones para sus mascotas | Ver todas, confirmar y marcar atención; revisar detalle, total y duración |
| Envíos de pedidos (Venta) | Elegir y pagar el envío al comprar; consultar su despacho | Gestionar tránsito y entrega |
| Servicios por sede (Institución) | Consultar prestaciones, precios y duración | Gestionar prestaciones y ofertas por sede |
| Logística (Envío) | Consultar coberturas durante el checkout | Gestionar transportistas, zonas y coberturas |
| Planes y suscripciones (Usuario) | Contratar, renovar, cancelar y consultar períodos propios | Administrar planes y auditar suscripciones |
| Pagos y pedidos | Ver únicamente los suyos | Consultar todos |

Los permisos se verifican también en el Gateway y los microservicios. Ocultar botones no es la protección: una petición directa de un cliente intentando editar sedes o acceder a datos ajenos se rechaza.

**Bienestar** conserva otra relación **muchos a muchos**: un profesional tiene varias especialidades y una especialidad pertenece a varios profesionales. La tabla de asociación tiene clave primaria compuesta y claves foráneas. Citas valida las referencias de mascota, sede y profesional mediante llamadas HTTP con identidad propagada y límites de tiempo.

## Parejas para la sustentación

| Pareja original | Transaccional (cabecera/detalle) | Maestro | N:M |
|---|---|---|---|
| Venta–Institución | Venta / DetalleVenta | Institución | Sedes ↔ prestaciones |
| Envío–Citas | Cita / DetalleCita | Envío: logística | Transportistas ↔ zonas |
| Catálogo–Usuario (Fio) | Suscripcion / PeriodoSuscripcion en Usuario | Catálogo | Clientes ↔ planes |

[Asignación, reglas, migración y demo por integrante](docs/asignacion-y-sustentacion.md). [Contraste con las sesiones 1–11 del ingeniero](docs/alineacion-pagatu.md).

El perfil confirma su guardado leyendo nuevamente la API. La edad de mascotas se registra en **días o meses**, con unidad explícita; las edades históricas en años se convierten a meses mediante migración. El despacho operativo pasa a Venta; el archivo histórico de Envío se conserva y el lanzador DEV lo migra sin duplicar ventas. Las N:M con atributos se implementan con entidades de asociación y claves foráneas locales.

## Manual de construcción desde cero

[Guía paso a paso, HTML copiable, PDF y fuentes por etapas](docs/manual-construccion-completa/README.md). Explica cómo crear y conectar todos los componentes desde una carpeta vacía.

## Ventas, fotos y comprobantes

[Guía de funciones y código](docs/ventas-imagenes-y-comprobantes.md): Ventas para ADMIN, Mis compras para CLIENTE, filtros y detalle; imagen principal local para productos/profesionales/sedes; constancia PDF imprimible para compras pagadas. Los pagos de demostración siguen disponibles.

## Abrir las aplicaciones

Las direcciones se abren **en la máquina donde ejecutas el proyecto**; no constituyen una publicación web de GitHub ni una URL externa de la nube.

| Aplicación | Dirección local | Acceso de demostración |
|---|---|---|
| Garritas Store | `http://localhost:4200` | `cliente` / `Cliente123!` |
| Kafka UI | `http://localhost:18085` | Clúster `garritas` |
| Keycloak | `http://localhost:18180/admin/` | `admin` / `local-admin-change-me` |
| Eureka | `http://localhost:18761` | Sin login |
| Gateway | `http://localhost:18080` | API con JWT |
| Grafana | `http://localhost:13000` | `admin` / `local-grafana` |
| Prometheus | `http://localhost:19090` | Sin login |

Administrador de la tienda: **`admin-store` / `Admin123!`**. Es distinto del administrador de Keycloak. Loki expone su API en 13100 y se consulta desde Grafana.

DEV incluye 16 productos para mascotas, seis sedes ficticias de Lima, Arequipa, Trujillo, Cusco y Huancayo, y profesionales/especialidades de ejemplo. Las migraciones repetibles de `db/demo` no sobrescriben datos existentes. El realm solo se importa cuando aún no existe. No uses estas identidades ni contraseñas de demostración para exponer el sistema en Internet.

El carrito conserva identificadores, cantidades, sede y clave de reintento, nunca tokens. El servidor determina precios, identidad y stock. La Saga reserva inventario, procesa un pago simulado y confirma o compensa. **TRANSFERENCIA** simula rechazo; el stock se devuelve antes de cancelar la venta.

## Manuales en PDF

1. [Ejecutar Garritas: instalación, puertos y diagnóstico](docs/manuales/01-Ejecucion-y-puertos.pdf).
2. [Construir desde cero: pasos, rutas y código completo](docs/manuales/02-Construccion-desde-cero-con-codigo.pdf).
3. [Entender arquitectura, clases, tecnologías y conexiones](docs/manuales/03-Arquitectura-clases-y-conexiones.pdf).

[Índice y evidencias de los manuales](docs/manuales/README.md). Se incluye un ZIP de fuentes sin dependencias/binarios, con manifiesto SHA-256; fue extraído y compilado en una carpeta nueva.

## Guía para la sustentación

[Guía completa en PDF](docs/sustentacion/Guia-de-sustentacion-Garritas.pdf), [resumen oral de dos páginas](docs/sustentacion/Resumen-para-exponer.pdf) y [mapa de código con rutas/líneas exactas](docs/sustentacion/Mapa-de-codigo.txt). Incluye once diagramas, fichas de los ocho servicios y respuestas a las siete preguntas S6–S11. [Índice y verificación](docs/sustentacion/README.md).

### Integración de mejoras y reglas de negocio

Consulta [la actualización de Catálogo, Usuario, delivery y paquetes](docs/integracion-fio-y-reglas-tienda.md) para conocer los cambios, las migraciones y sus límites.

### Guía de estudio C4: Catálogo y Usuario

[HTML, PDF, diagramas y mapa de código](docs/guia-estudio-catalogo-usuario/README.md). Incluye los cuatro niveles C4, responsabilidades, CRUD, Saga/Kafka, compensación, seguridad y credenciales de demostración.

## Uso rápido y pruebas opcionales

Requisitos: **JDK 21 completo, Node 24, Docker Compose, Git** y Python 3 para las herramientas Linux/pruebas. Los ejemplos son locales; no se hacen cobros bancarios reales.

### Linux o WSL2

Desde la raíz:

```bash
bash uso-rapido/scripts/dev.sh build
bash uso-rapido/scripts/dev.sh all
bash uso-rapido/scripts/dev.sh status
```

`build` hace una compilación limpia para empaquetar también los cambios del soporte común; compila todos los servicios e instala el soporte común para permitir también arranques manuales por módulo. `all` inicia Kafka, Keycloak, las ocho bases de negocio, Config Server, Eureka, los ocho servicios, Gateway y Angular. Si faltan dependencias frontend, ejecuta `npm ci` antes de iniciar su servidor.

Observabilidad opcional:

```bash
bash uso-rapido/scripts/dev.sh observability
bash uso-rapido/scripts/dev.sh status --observability
```

### Ejemplo de Kafka

El ejemplo equivalente al de Pagatu está en [`uso-rapido/garritas-eventos-py`](uso-rapido/garritas-eventos-py/README.md). Tiene productor, consumidor, requisitos y Compose. Usa un topic de demostración separado para no crear compras ficticias en la Saga real.

### Pruebas y documentación

Con DEV iniciado:

```bash
bash uso-rapido/scripts/dev.sh test
(cd clients/garritas-frontend && npm test && npm run build)
python3 -m pip install -r uso-rapido/scripts/requirements-test.txt
CHROMIUM_PATH=/usr/bin/chromium python3 uso-rapido/scripts/domain_smoke.py
CHROMIUM_PATH=/usr/bin/chromium python3 uso-rapido/scripts/academic_smoke.py
CHROMIUM_PATH=/usr/bin/chromium python3 uso-rapido/scripts/smoke.py
CHROMIUM_PATH=/usr/bin/chromium python3 uso-rapido/scripts/consoles.py
```

Si no usas Chromium del sistema, instala el navegador de Playwright con `python3 -m playwright install chromium` y omite `CHROMIUM_PATH`. `domain_smoke.py` prueba todos los dominios con ADMIN y dos CLIENTE: propiedad, permisos, asociación muchos a muchos, cita, compra y entrega. Los registros de prueba se identifican como tales; los historiales de ventas y citas se conservan.

- [Guía de ejecución y diagnóstico](docs/ejecucion.md)
- [Arquitectura y decisiones](docs/arquitectura.md)
- [Resultados y límites de validación](docs/validacion.md)
- [Compose integrado opcional](uso-rapido/docker/README.md)

La documentación puede construirse con `pip install -r docs/requirements.txt` y `mkdocs build --strict`.
