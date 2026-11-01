# Indicadores de evaluación → dónde está en el proyecto

Guía para la presentación oral. Cada indicador de la rúbrica apunta al archivo y la línea donde se demuestra.

## Base de Datos (5 pts)

| Indicador | Evidencia |
|---|---|
| Implementación | `base_datos.sql`: 11 tablas (`usuarios`, `planes`, `rutinas`, `rutina_ejercicios`, `socios`, `asistencias`, `ejercicios_realizados`, `registros_peso`, `pagos`, `congelamientos`, `auditoria_socios`) con claves foráneas (por ejemplo, líneas 85, 103 y 129), un `UNIQUE` que impide dos entradas el mismo día (línea 102) y datos de ejemplo. `migraciones/` actualiza una base existente sin recrearla. |
| C.R.U.D. | **C**reate: alta de socio (`app.py:539`), check-in (`app.py:732`), nuevo peso (`app.py:1065`). **R**ead: lista y ficha (`app.py:511`, `app.py:640`). **U**pdate: editar datos del socio (`app.py:610`, formulario "Editar datos" en `socio.html`), renovar plan y actualizar peso mediante el trigger (`base_datos.sql:179`). **D**elete: eliminar socio (`app.py:587`). |
| Conexión desde Python | `conectar()` en `app.py:63` con `mysql.connector`. Las funciones `consultar`, `consultar_uno` y `ejecutar` (`app.py:74-100`) evitan repetir código y usan consultas parametrizadas (`%s`). `transaccion()` (`app.py:104`) confirma o deshace varias escrituras juntas. |

## Python (10 pts)

| Indicador | Evidencia |
|---|---|
| Manejo de rutas | 22 rutas Flask con `@app.route`: `/`, `/api/login`, `/api/usuarios`, `/api/planes`, `/api/socios`, `/api/socios/<int:socio_id>` y sus sub-rutas. Usan métodos GET, POST, PUT, PATCH y DELETE. |
| Conexión con el cliente | Flask sirve `static/` desde la raíz (`app.py:20`) y expone la API JSON que consume `fetch` en `app.js:13`. |
| Paso de información con el cliente | Entrada: `request.get_json()` dentro de `leer_json()` (`app.py:137`). Salida: `jsonify(...)`. Los errores usan `error()` con código HTTP (`app.py:119`). Los parámetros de URL (`<int:socio_id>`) también pasan datos. `request.args` lee `q` y `estado` en `app.py:513`. |
| Lógica (iteradores y condicionales) | Bucle `for` que valida campos obligatorios (`app.py:177`, dentro de `validar_datos_socio`). Bucle `for` que calcula el estado de cada socio (`app.py:523`). Condicionales en las reglas: `calcular_estado`, `calcular_imc` y `calcular_progreso` (`app.py:235-286`) y en el check-in (`app.py:744-764`). |
| Funciona sin errores | Validaciones antes de operar (`validar_datos_socio`, `app.py:176`): números, valores permitidos, largo de los textos, CI duplicado y plan inexistente, siempre con un error 400 y un mensaje claro. Alta, eliminación y registro de peso se guardan en una transacción. Las reglas tienen pruebas en `tests/test_reglas.py`. |

## JavaScript (5 pts)

| Indicador | Evidencia |
|---|---|
| Lógica (iteradores y condicionales) | `for...of` para pintar la tabla de socios (`app.js:193`, con plantillas de texto), los planes (`app.js:79`) y el historial de peso (`app.js:391`). Condicionales en `mostrarMensaje`, en el color del progreso (`mostrarProgreso`, `app.js:367`) y en `confirm()` antes de eliminar (`app.js:246`). |
| Funciona sin errores | Todas las llamadas pasan por `llamarApi` (`app.js:13`) y se muestra el mensaje o el error de la API (`mostrarResultado`, `app.js:46`). |
| Recibe y procesa información | Lee el JSON de la API y lo transforma: `formatearFecha`, `etiquetaEstado`, el IMC con su categoría, el signo `+` en la diferencia de peso. Lee el `?id=` de la URL (`app.js:294`). `escaparHtml` (`app.js:56`) muestra como texto el HTML que venga en los datos. `cargarFicha()` reparte los datos en funciones cortas (`mostrarDatos`, `mostrarPlan`, `mostrarSalud`, `mostrarProgreso`, `mostrarHistorial`, `mostrarAuditoria`). |

## HTML (5 pts)

| Indicador | Evidencia |
|---|---|
| Construcción de la página | `static/login.html` (entrada), `static/index.html` (lista y alta), `static/socio.html` (ficha) y `static/usuarios.html` (usuarios). Etiquetas semánticas: `header`, `main`, `section`, `table`, `form`, `label`. |
| Funcionamiento coordinado con el servidor | Las tablas y los desplegables se rellenan desde la API (`cargarSocios()`, `cargarPlanes()`). El formulario envía los datos con `onsubmit="darDeAlta(event)"`. |
| Navegabilidad entre páginas | `login.html` → `index.html` → `socio.html?id=N` (botón "Ver ficha") → "← Volver" (`socio.html:11`). `index.html` → `usuarios.html` para el administrador. Sin sesión, `llamarApi` redirige a `login.html`. |
| Estructura | `<!DOCTYPE html>`, `lang="es"`, `meta viewport`, `title`, `head` y `body` en todas las páginas. |

## Hojas de estilo y CSS (5 + 5 pts)

| Indicador | Evidencia |
|---|---|
| Manejo de espacios | `margin`, `padding`, `gap`, `max-width: 900px` centrado. `display: grid` en `.campos` y `.columnas`. `@media (max-width: 600px)` pasa a una columna. |
| Construcción visual | Cabecera oscura, secciones tipo tarjeta, etiquetas de colores para el estado (`.activo`, `.por-vencer`, `.vencido`), mensajes verdes y rojos. |
| Importación | `<link rel="stylesheet" href="estilos.css">` en las cuatro páginas. |
| Reutilización | Un solo `estilos.css` para todas las páginas. Clases reutilizables: `.boton` (sirve para `<button>` y `<a>`), `.estado`, `.mensaje`, `.columnas`. |
| Aplicación de estilos a etiquetas | Selectores de etiqueta: `body`, `header`, `main`, `section`, `table`, `th, td`, `input, select`, `label`. |
| Eventos `:hover` | `button:hover, .boton:hover` (`estilos.css:195`) y `.boton-eliminar:hover` (`estilos.css:224`). |

## Reglas nuevas pedidas por el profesor

| Pedido | Evidencia |
|---|---|
| Lista de búsqueda | T2: `listar_socios` (`app.py:512`) valida los cinco estados, busca por nombre o CI con parámetros y escapa los comodines de LIKE. `buscarSocios`, `limpiarBusqueda` y `cargarSocios` (`app.js:184-227`) usan el formulario (`index.html:22`) y muestran "No se encontraron socios". `TestBusqueda` en `tests/test_reglas.py` cubre los filtros sin MySQL. |
| Triggers y auditoría | T4: `copiar_peso_socio` (`base_datos.sql:179`) actualiza el peso; `auditar_plan_socio` (`base_datos.sql:184`) compara plan/vencimiento y registra solo cambios. Migración repetible `migraciones/004_triggers.sql`. La ficha consulta `auditoria` (`app.py:690`) y la muestra con `escaparHtml` (`app.js:413`, `socio.html:147`). Eliminar borra la auditoría dentro de la transacción (`app.py:604`). Congelar/descongelar también se auditan (`app.py:853`, `app.py:892`). |
| Días sumados en el pago | Regla 7: `calcular_dias_restantes` y `guardar_pago` en `app.py`, tabla `pagos` en `base_datos.sql`, historial en la ficha (`mostrarPagos` en `app.js`). |
| Cancelados | Regla 8: `cancelar_socio` en `app.py`, columna `fecha_cancelacion`, estado calculado en `calcular_estado`. |
| Congelar plan (agregado) | Regla 9: `congelar_plan` y `descongelar_plan` en `app.py`, tabla `congelamientos`. No hace falta una tarea programada, porque el estado sale de comparar fechas. |
| Rutina por día | Reglas 11 y 12: `calcular_siguiente_dia` en el check-in, `armar_seguimiento` y `marcar_ejercicio` en `app.py`, tablas `rutina_ejercicios` y `ejercicios_realizados`, `mostrarSeguimiento` en `app.js`. |
| Asistencia y subir de nivel (agregados) | Reglas 13 y 14: `calcular_asistencia`, `calcular_nivel_sugerido` y `subir_nivel` en `app.py`. |
| Login y listado | Regla 15: `exigir_sesion`, `solo_admin` e `iniciar_sesion` en `app.py`, tabla `usuarios`, `login.html` y `usuarios.html`. Las contraseñas se guardan con el hash de Werkzeug. |

## Funcionamiento y conocimiento del sistema (1 pt)

Resumen para explicar en 30 segundos:

1. El navegador carga `index.html` y `app.js` llama a `/api/socios`.
2. Flask recibe la petición, consulta MySQL con `consultar()` y aplica las reglas (estado, IMC, progreso, check-in).
3. Flask devuelve JSON y `app.js` lo pinta en la tabla.

Evidencia de T2: 40 pruebas en verde con `python -m unittest tests.test_reglas` (7 nuevas). Se verificó también la sintaxis de JavaScript con `node --check static/app.js`. La prueba de la app contra un MySQL separado está pendiente; no se importó `base_datos.sql` ni se utilizó el puerto 3306. Los casos para la presentación están en el README, sección "Búsqueda de socios (T2)".

Evidencia T4: 33 pruebas sin base (`tests/test_reglas.py`) y 7 pruebas reales (`tests/test_triggers.py`) en verde sobre MySQL 8.4.5 (3309) y MariaDB 11.4.5 (3308). Cubren copia de peso, cambio de plan/vencimiento, ausencia de cambios, congelar/descongelar, rollback, eliminación y repetición de la migración conservando el historial. Se importaron ambos SQL con los clientes de ambos motores y con phpMyAdmin 5.2.2 (PHP 8.3.20), repitiendo la migración desde su pestaña Importar. Se comprobó la ficha en Chrome a 1280 y 390 píxeles, con login, auditoría llena/vacía y escape de HTML; `node --check static/app.js` también pasó. No se usó el puerto 3306. Pasos y casos de presentación: README, sección "Triggers y auditoría (T4)".

Las reglas del gimnasio están en el README, sección "Reglas del gimnasio".

## Modificación solicitada (5 pts): puntos de cambio

Dónde tocar según lo que pidan:

| Si piden... | Se toca |
|---|---|
| Una regla nueva o distinta (por ejemplo, otros días de aviso de vencimiento) | La función de la regla en `app.py:218-286`, y su prueba en `tests/test_reglas.py`. |
| Un campo nuevo en el socio | Columna en `base_datos.sql`, `INSERT` y `SELECT` en `app.py`, formulario en `index.html`, dato en `app.js`. |
| Un botón o acción nueva | Ruta en `app.py`, botón en el HTML y función en `app.js` con `llamarApi`. |
| Un cambio visual | Clase nueva en `estilos.css` (por ejemplo, otro `:hover`). |

## Puntos débiles a tener en cuenta

- **Duplicado en el check-in:** la consulta de "ya entró hoy" y la de "últimos 7 días" son dos SQL distintos. Es intencional, porque miden cosas diferentes. Además, el `UNIQUE` de `asistencias` frena dos entradas simultáneas, que la consulta sola no puede detectar.
