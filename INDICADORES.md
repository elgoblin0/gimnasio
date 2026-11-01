# Indicadores de evaluación → dónde está en el proyecto

Guía para la presentación oral. Cada indicador de la rúbrica apunta al archivo y la línea donde se demuestra.

## Base de Datos (5 pts)

| Indicador | Evidencia |
|---|---|
| Implementación | `base_datos.sql`: 5 tablas (`planes`, `rutinas`, `socios`, `asistencias`, `registros_peso`) con claves foráneas (líneas 52, 67, 79), un `UNIQUE` que impide dos entradas el mismo día (línea 66) y datos de ejemplo. `migraciones/` actualiza una base existente sin recrearla. |
| C.R.U.D. | **C**reate: alta de socio (`app.py:272`), check-in (`app.py:426`), nuevo peso (`app.py:490`). **R**ead: lista y ficha (`app.py:258`, `app.py:361`). **U**pdate: editar datos del socio (`app.py:331`, formulario "Editar datos" en `socio.html`), renovar plan y actualizar peso. **D**elete: eliminar socio (`app.py:317`). |
| Conexión desde Python | `conectar()` en `app.py:33` con `mysql.connector`. Las funciones `consultar`, `consultar_uno` y `ejecutar` (`app.py:44-70`) evitan repetir código y usan consultas parametrizadas (`%s`). `transaccion()` (`app.py:74`) confirma o deshace varias escrituras juntas. |

## Python (10 pts)

| Indicador | Evidencia |
|---|---|
| Manejo de rutas | 10 rutas Flask con `@app.route`: `/`, `/api/planes`, `/api/socios`, `/api/socios/<int:socio_id>` y sus sub-rutas. Usan métodos GET, POST, PUT y DELETE. |
| Conexión con el cliente | Flask sirve `static/` desde la raíz (`app.py:17`) y expone la API JSON que consume `fetch` en `app.js:13`. |
| Paso de información con el cliente | Entrada: `request.get_json()` dentro de `leer_json()` (`app.py:98`). Salida: `jsonify(...)`. Los errores usan `error()` con código HTTP (`app.py:89`). Los parámetros de URL (`<int:socio_id>`) también pasan datos. |
| Lógica (iteradores y condicionales) | Bucle `for` que valida campos obligatorios (`app.py:138`, dentro de `validar_datos_socio`). Bucle `for` que calcula el estado de cada socio (`app.py:265`). Condicionales en las reglas: `calcular_estado`, `calcular_imc` y `calcular_progreso` (`app.py:186-224`) y en el check-in (`app.py:437-452`). |
| Funciona sin errores | Validaciones antes de operar (`validar_datos_socio`, `app.py:137`): números, valores permitidos, largo de los textos, CI duplicado y plan inexistente, siempre con un error 400 y un mensaje claro. Alta, eliminación y registro de peso se guardan en una transacción. Las reglas tienen pruebas en `tests/test_reglas.py`. |

## JavaScript (5 pts)

| Indicador | Evidencia |
|---|---|
| Lógica (iteradores y condicionales) | `for...of` para pintar la tabla de socios (`app.js:92`, con plantillas de texto), los planes (`app.js:71`) y el historial de peso (`app.js:252`). Condicionales en `mostrarMensaje`, en el color del progreso (`mostrarProgreso`, `app.js:228`) y en `confirm()` antes de eliminar (`app.js:118`). |
| Funciona sin errores | Todas las llamadas pasan por `llamarApi` (`app.js:13`) y se muestra el mensaje o el error de la API (`mostrarResultado`, `app.js:38`). |
| Recibe y procesa información | Lee el JSON de la API y lo transforma: `formatearFecha`, `etiquetaEstado`, el IMC con su categoría, el signo `+` en la diferencia de peso. Lee el `?id=` de la URL (`app.js:166`). `escaparHtml` (`app.js:48`) muestra como texto el HTML que venga en los datos. `cargarFicha()` reparte los datos en funciones cortas (`mostrarDatos`, `mostrarPlan`, `mostrarSalud`, `mostrarProgreso`, `mostrarHistorial`). |

## HTML (5 pts)

| Indicador | Evidencia |
|---|---|
| Construcción de la página | `static/index.html` (lista y alta) y `static/socio.html` (ficha). Etiquetas semánticas: `header`, `main`, `section`, `table`, `form`, `label`. |
| Funcionamiento coordinado con el servidor | Las tablas y los desplegables se rellenan desde la API (`cargarSocios()`, `cargarPlanes()`). El formulario envía los datos con `onsubmit="darDeAlta(event)"`. |
| Navegabilidad entre páginas | `index.html` → `socio.html?id=N` (botón "Ver ficha") → "← Volver" (`socio.html:11`). |
| Estructura | `<!DOCTYPE html>`, `lang="es"`, `meta viewport`, `title`, `head` y `body` en las dos páginas. |

## Hojas de estilo y CSS (5 + 5 pts)

| Indicador | Evidencia |
|---|---|
| Manejo de espacios | `margin`, `padding`, `gap`, `max-width: 900px` centrado. `display: grid` en `.campos` y `.columnas`. `@media (max-width: 600px)` pasa a una columna. |
| Construcción visual | Cabecera oscura, secciones tipo tarjeta, etiquetas de colores para el estado (`.activo`, `.por-vencer`, `.vencido`), mensajes verdes y rojos. |
| Importación | `<link rel="stylesheet" href="estilos.css">` en las dos páginas. |
| Reutilización | Un solo `estilos.css` para ambas páginas. Clases reutilizables: `.boton` (sirve para `<button>` y `<a>`), `.estado`, `.mensaje`, `.columnas`. |
| Aplicación de estilos a etiquetas | Selectores de etiqueta: `body`, `header`, `main`, `section`, `table`, `th, td`, `input, select`, `label`. |
| Eventos `:hover` | `button:hover, .boton:hover` (`estilos.css:153`) y `.boton-eliminar:hover` (`estilos.css:182`). |

## Funcionamiento y conocimiento del sistema (1 pt)

Resumen para explicar en 30 segundos:

1. El navegador carga `index.html` y `app.js` llama a `/api/socios`.
2. Flask recibe la petición, consulta MySQL con `consultar()` y aplica las reglas (estado, IMC, progreso, check-in).
3. Flask devuelve JSON y `app.js` lo pinta en la tabla.

Las 6 reglas del gimnasio están en el README, sección "Reglas del gimnasio".

## Modificación solicitada (5 pts): puntos de cambio

Dónde tocar según lo que pidan:

| Si piden... | Se toca |
|---|---|
| Una regla nueva o distinta (por ejemplo, otros días de aviso de vencimiento) | La función de la regla en `app.py:176-224`, y su prueba en `tests/test_reglas.py`. |
| Un campo nuevo en el socio | Columna en `base_datos.sql`, `INSERT` y `SELECT` en `app.py`, formulario en `index.html`, dato en `app.js`. |
| Un botón o acción nueva | Ruta en `app.py`, botón en el HTML y función en `app.js` con `llamarApi`. |
| Un cambio visual | Clase nueva en `estilos.css` (por ejemplo, otro `:hover`). |

## Puntos débiles a tener en cuenta

- **Duplicado en el check-in:** la consulta de "ya entró hoy" y la de "últimos 7 días" son dos SQL distintos. Es intencional, porque miden cosas diferentes. Además, el `UNIQUE` de `asistencias` frena dos entradas simultáneas, que la consulta sola no puede detectar.
