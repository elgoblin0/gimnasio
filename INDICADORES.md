# Indicadores de evaluación → dónde está en el proyecto

Guía para la presentación oral. Cada indicador de la rúbrica apunta al archivo y la línea donde se demuestra.

## Base de Datos (5 pts)

| Indicador | Evidencia |
|---|---|
| Implementación | `base_datos.sql`: 5 tablas (`planes`, `rutinas`, `socios`, `asistencias`, `registros_peso`) con claves foráneas (líneas 52, 63, 75) y datos de ejemplo. `migraciones/001_dni_a_ci.sql` renombra una columna sin perder datos. |
| C.R.U.D. | **C**reate: alta de socio (`app.py:166`), check-in (`app.py:349`), nuevo peso (`app.py:405`). **R**ead: lista y ficha (`app.py:152`, `app.py:284`). **U**pdate: editar datos del socio (`app.py:254`, formulario "Editar datos" en `socio.html`), renovar plan y actualizar peso. **D**elete: eliminar socio (`app.py:210`). |
| Conexión desde Python | `conectar()` en `app.py:21` con `mysql.connector`. Las funciones `consultar`, `consultar_uno` y `ejecutar` (`app.py:32-58`) usan consultas parametrizadas (`%s`). |

## Python (10 pts)

| Indicador | Evidencia |
|---|---|
| Manejo de rutas | 10 rutas Flask con `@app.route`: `/`, `/api/planes`, `/api/socios`, `/api/socios/<int:socio_id>` y sus sub-rutas. Usan métodos GET, POST, PUT y DELETE. |
| Conexión con el cliente | Flask sirve `static/` desde la raíz (`app.py:14`) y expone la API JSON que consume `fetch` en `app.js:13`. |
| Paso de información con el cliente | Entrada: `request.get_json()` (`app.py:168`). Salida: `jsonify(...)`. Los errores usan `error()` con código HTTP (`app.py:61`). Los parámetros de URL (`<int:socio_id>`) también pasan datos. |
| Lógica (iteradores y condicionales) | Bucle `for` que valida campos obligatorios (`app.py:172`). Bucle `for` que calcula el estado de cada socio (`app.py:159`). Condicionales en las reglas: `calcular_estado`, `calcular_imc` y `calcular_progreso` (`app.py:81-118`) y en el check-in (`app.py:361-375`). |
| Funciona sin errores | Validaciones antes de operar (peso, altura, CI duplicado, plan inexistente). Uso de `try/except/finally` con `rollback` en el borrado (`app.py:215-251`). |

## JavaScript (5 pts)

| Indicador | Evidencia |
|---|---|
| Lógica (iteradores y condicionales) | `for...of` para pintar la tabla de socios (`app.js:84`), los planes (`app.js:63`) y el historial de peso (`app.js:216`). Condicionales en `mostrarMensaje`, en el color del progreso (`app.js:197-211`) y en `confirm()` antes de eliminar (`app.js:110-118`). |
| Funciona sin errores | Todas las llamadas pasan por `llamarApi` (`app.js:13`) y se muestra el mensaje o el error de la API (`mostrarResultado`, `app.js:38`). |
| Recibe y procesa información | Lee el JSON de la API y lo transforma: `formatearFecha`, `etiquetaEstado`, el IMC con su categoría, el signo `+` en la diferencia de peso. Lee el `?id=` de la URL (`app.js:158`). |

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
| Una regla nueva o distinta (por ejemplo, otros días de aviso de vencimiento) | La función de la regla en `app.py:70-118`. |
| Un campo nuevo en el socio | Columna en `base_datos.sql`, `INSERT` y `SELECT` en `app.py`, formulario en `index.html`, dato en `app.js`. |
| Un botón o acción nueva | Ruta en `app.py`, botón en el HTML y función en `app.js` con `llamarApi`. |
| Un cambio visual | Clase nueva en `estilos.css` (por ejemplo, otro `:hover`). |

## Puntos débiles a tener en cuenta

- **Seguridad en el frontend:** `app.js` arma el HTML concatenando texto (`innerHTML +=`). Un nombre con `<script>` se inyectaría. En un proyecto de facultad es aceptable, pero conviene saber explicarlo.
- **Duplicado en el check-in:** la consulta de "ya entró hoy" y la de "últimos 7 días" son dos SQL distintos. Es intencional, porque miden cosas diferentes.
