# Guías individuales para estudiar y sustentar

Dos PDF independientes con explicación del negocio, conexiones, relaciones, ubicación exacta del código, guion de demostración y preguntas de defensa.

- **[Fio: Catálogo y Usuario](Fio-Catalogo-y-Usuario.pdf)**. Productos/categorías, CRUD y paginación, fotos locales, inventario y compensación, cuenta propia, mascotas, roles internos, planes, suscripciones y períodos. Distingue seguridad de Keycloak de las tablas del negocio.
- **[Deissy: Citas y Envío](Deissy-Citas-y-Envio.pdf)**. Reserva transaccional, prestaciones/paquetes, propiedad, control de agenda, cobertura logística N:M, tarifa cobrada y conexión con el despacho que pertenece a Venta.

Empiecen por los capítulos explicativos y el guion de tres minutos. Después utilicen **el índice navegable y Ctrl+F** para consultar el mapa de archivos y el código completo. En VS Code: **Ctrl+P** con la ruta y **Ctrl+G** con la línea. Los enlaces del PDF abren el código fijado en GitHub.

Los anexos incluyen los Java de `src/main` y `src/test` de sus dos dominios, SQL, configuración, pantallas Angular asignadas y soporte compartido relevante. La numeración de línea es de estudio: no se debe pegar como parte del programa. Esto no sustituye el manual de reconstrucción del proyecto entero.

## Versión y verificación

La referencia es `6e2239c55884c2a6ae53dd921147d9e5b53749ab` de `Nikol235/Garritas-Store`. Las guías no modifican la aplicación. El pago sigue simulado, las suscripciones no cobran dinero real y el despacho se conserva en Venta.

[Resultado de verificación](verificacion.json): líneas y hashes contra Git, integridad de todos los archivos reproducidos, cobertura de clases/pruebas, texto seleccionable, marcadores/enlaces y ausencia de páginas vacías o desbordamiento horizontal. Es verificación documental; no repite la ejecución funcional del sistema.

## Regenerar

Se necesita Graphviz (`dot`), Python y las bibliotecas de `requirements.txt`.

```bash
python docs/guias-integrantes/generar.py
python docs/guias-integrantes/verificar.py
```

Los Markdown son fuentes para auditar el texto y los bloques completos; las ilustraciones están en `diagramas/`. Se mantiene atribución al enfoque docente de [Pagatu](https://262dist.github.io/pagatu/) y se distingue la responsabilidad de cada integrante del código compartido.
