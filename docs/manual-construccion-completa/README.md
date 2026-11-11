# Construir Garritas Store desde cero

Empieza por [el manual paso a paso en HTML](00-Manual-paso-a-paso.html) o [su PDF](00-Manual-paso-a-paso.pdf). Explica desde el nombre y las carpetas hasta el arranque, la demostración y la publicación en tu propio GitHub.

El [paquete completo ZIP](Garritas-desde-cero.zip) permite trabajar sin tener que descargar cada archivo. Contiene el manual HTML, el catálogo de código HTML, los cinco PDF, las fuentes originales, listas por etapa y un ayudante PowerShell que conserva los archivos existentes si detecta diferencias.

| Material | Contenido |
|---|---|
| [Manual paso a paso](00-Manual-paso-a-paso.pdf) | Instalación, nombres, estructura, creación de capas, conexión, explicación y comprobaciones |
| [Código copiable y buscable](01-Codigo-completo.html) | Ficha de cada archivo, ruta, función y contenido completo; botones para copiar |
| [Código de infraestructura](02-Codigo-infraestructura.pdf) | Común, Config, Eureka, seguridad, Keycloak, Kafka, Gateway y observabilidad |
| [Código de maestros](03-Codigo-maestros.pdf) | Catálogo, Institución, Bienestar y Envío |
| [Código de transacciones](04-Codigo-transacciones.pdf) | Usuario, Venta, Pago y Citas |
| [Código Angular y herramientas](05-Codigo-Angular-y-herramientas.pdf) | Frontend, scripts, pruebas y despliegue integrado alternativo |
| [Comandos en texto](Comandos-copiables.txt) | Arranque desde la raíz de la construcción |

Las rutas se interpretan desde una carpeta nueva `Garritas-desde-cero`. No se necesita clonar para reconstruir. Los comandos de clonación se explican como alternativa para comparar con el proyecto existente.

El código de referencia está fijado en `5b61028187528a9b7918715e1661bb6a7d50a723`: 529 archivos de aplicación/configuración/herramientas; 478 se imprimen íntegros. Los wrappers, el lock de npm y archivos vacíos de soporte están completos en el ZIP y referenciados en el catálogo. Se excluyen documentación anterior, personalización de su sitio y `.env`; DEV utiliza los valores de sus Compose y conserva `.env.example` para consultar el modo alternativo.

## Leer y copiar

Descarga el ZIP y extráelo. Abre `00-Manual-paso-a-paso.html` con tu navegador; desde sus anexos abre las fichas de `01-Codigo-completo.html`. El botón **Copiar código** copia el bloque sin encabezados ni números de línea. Para los archivos generados usa el original de `FUENTES`.

Los PDF tienen texto seleccionable e índice con marcadores. Un lector PDF puede introducir saltos visuales al copiar: para pegar archivos largos el HTML y las fuentes del ZIP son la referencia exacta.

## Generar y verificar

Requiere Python con `playwright` y `PyMuPDF`, más Chromium en `/usr/bin/chromium`.

```bash
python docs/manual-construccion-completa/generar.py
python docs/manual-construccion-completa/verificar.py
```

[Verificación documental](verificacion.json): rutas y hashes contra el commit, correspondencia íntegra de cada bloque, contenido del ZIP, texto/marcadores PDF, navegación, búsqueda y botón de copia HTML. Esta comprobación no ejecuta PowerShell ni vuelve a afirmar pruebas funcionales de la aplicación en Windows.

El enfoque sigue las sesiones 1–11 de [Pagatu](https://262dist.github.io/pagatu/), de Ángel Sullon Macalupu, adaptado al dominio Garritas. El manual explica expresamente pago simulado, límites de la Saga y diferencia entre maestro, transacción local y compensación.
