# Indicadores de evaluación → dónde está en el proyecto

Guía para la presentación oral. Cada indicador de la rúbrica apunta al archivo y la línea donde se demuestra.

## Base de Datos (5 pts)

| Indicador | Evidencia |
|---|---|
| Implementación | `base_datos.sql`: 11 tablas (`usuarios`, `planes`, `rutinas`, `rutina_ejercicios`, `socios`, `asistencias`, `ejercicios_realizados`, `registros_peso`, `pagos`, `congelamientos`, `auditoria_socios`) con claves foráneas (por ejemplo, líneas 86, 105 y 131), un `UNIQUE` que impide dos entradas el mismo día (línea 104) y datos de ejemplo. `migraciones/` actualiza una base existente sin recrearla. |
| C.R.U.D. | **C**reate: alta de socio (`app.py:617`), check-in (`app.py:820`), nuevo peso (`app.py:1256`). **R**ead: lista y ficha (`app.py:571`, `app.py:724`). **U**pdate: editar datos del socio (`app.py:688`, pestaña Editar en `socio.html`), renovar plan, registrar la salida (`app.py:877`) y actualizar peso mediante el trigger (`base_datos.sql:180`). **D**elete: eliminar socio (`app.py:665`). |
| Conexión desde Python | `conectar()` en `app.py:77` con `mysql.connector`. Las funciones `consultar`, `consultar_uno` y `ejecutar` (`app.py:88-114`) evitan repetir código y usan consultas parametrizadas (`%s`). `transaccion()` (`app.py:118`) confirma o deshace varias escrituras juntas. |

## Python (10 pts)

| Indicador | Evidencia |
|---|---|
| Manejo de rutas | 26 rutas Flask con `@app.route`: `/`, `/api/login`, `/api/usuarios`, `/api/planes`, `/api/dashboard`, `/api/socios`, `/api/socios/<int:socio_id>` y sus sub-rutas. Usan métodos GET, POST, PUT, PATCH y DELETE. |
| Conexión con el cliente | Flask sirve `static/` desde la raíz (`app.py:20`) y expone la API JSON que consume `fetch` en `app.js:13`. |
| Paso de información con el cliente | Entrada: `request.get_json()` dentro de `leer_json()` (`app.py:151`). Salida: `jsonify(...)`. Los errores usan `error()` con código HTTP (`app.py:133`). Los parámetros de URL (`<int:socio_id>`) también pasan datos. `request.args` lee `q` y `estado` en `app.py:573`. |
| Lógica (iteradores y condicionales) | Bucle `for` que valida campos obligatorios (`app.py:191`, dentro de `validar_datos_socio`). Bucle `for` que calcula el estado de cada socio (`app.py:597`). Condicionales en las reglas: `calcular_estado`, `calcular_imc` y `calcular_progreso` (`app.py:249-346`) y en el check-in (`app.py:828-870`). |
| Funciona sin errores | Validaciones antes de operar (`validar_datos_socio`, `app.py:190`): números, valores permitidos, largo de los textos, CI duplicado y plan inexistente, siempre con un error 400 y un mensaje claro. Alta, eliminación y registro de peso se guardan en una transacción. Las reglas tienen pruebas en `tests/test_reglas.py`. |

## JavaScript (5 pts)

| Indicador | Evidencia |
|---|---|
| Lógica (iteradores y condicionales) | `for...of` para pintar la tabla de socios (`app.js:233`, con plantillas de texto), los planes (`app.js:100`) y el historial de peso (`app.js:725`). Condicionales en `mostrarMensaje`, en el color del progreso (`mostrarProgreso`, `app.js:701`) y en `confirm()` antes de eliminar (`app.js:298`). |
| Funciona sin errores | Todas las llamadas pasan por `llamarApi` (`app.js:13`) y se muestra el mensaje o el error de la API (`mostrarResultado`, `app.js:46`). |
| Recibe y procesa información | Lee el JSON de la API y lo transforma: `formatearFecha`, `etiquetaEstado`, el IMC con su categoría, el signo `+` en la diferencia de peso. Lee el `?id=` de la URL (`app.js:623`). `escaparHtml` (`app.js:56`) muestra como texto el HTML que venga en los datos. `cargarFicha()` reparte los datos en funciones cortas (`mostrarDatos`, `mostrarPlan`, `mostrarSalud`, `mostrarProgreso`, `mostrarHistorial`, `mostrarAuditoria`). |

## HTML (5 pts)

| Indicador | Evidencia |
|---|---|
| Construcción de la página | `static/login.html` (entrada), `static/index.html` (lista y alta), `static/socio.html` (ficha en pestañas), `static/dashboard.html` (dashboard), `static/planes.html` (precios) y `static/usuarios.html` (usuarios). Etiquetas semánticas: `header`, `nav`, `main`, `section`, `table`, `form`, `label`. |
| Funcionamiento coordinado con el servidor | Las tablas y los desplegables se rellenan desde la API (`cargarSocios()`, `cargarPlanes()`). El formulario envía los datos con `onsubmit="darDeAlta(event)"`. |
| Navegabilidad entre páginas | `login.html` → `index.html` → `socio.html?id=N` (botón "Ver ficha") → "← Socios". La barra de arriba lleva a Socios, Dashboard y, para el administrador, Planes y Usuarios. Sin sesión, `llamarApi` redirige a `login.html`. |
| Estructura | `<!DOCTYPE html>`, `lang="es"`, `meta viewport`, `title`, `head` y `body` en todas las páginas. |

## Hojas de estilo y CSS (5 + 5 pts)

| Indicador | Evidencia |
|---|---|
| Manejo de espacios | `margin`, `padding`, `gap`, `max-width: 1120px` centrado (`estilos.css:118`). `display: grid` en `.columnas` (`estilos.css:183`), `.campos` (`estilos.css:327`) y `.tarjetas` (`estilos.css:481`, con `auto-fit` para el dashboard). `@media (max-width: 700px)` (`estilos.css:840`) reordena la barra, reduce los márgenes y pasa la búsqueda a una columna. |
| Construcción visual | Barra de arriba con el logo, secciones tipo tarjeta, un punto de color para cada estado (`.activo`, `.por-vencer`, `.vencido`, `.congelado`, `.cancelado`, `estilos.css:308-312`), mensajes verdes y rojos (`.mensaje.ok`, `.mensaje.error`). |
| Importación | `<link rel="stylesheet" href="estilos.css">` en las seis páginas, además de las fuentes de Google Fonts. |
| Reutilización | Un solo `estilos.css` para todas las páginas. Clases reutilizables: `.boton` (sirve para `<button>` y `<a>`), `.estado`, `.mensaje`, `.columnas`. |
| Aplicación de estilos a etiquetas | Selectores de etiqueta: `body`, `header`, `main`, `section`, `table`, `th, td`, `input, select`, `label`. |
| Eventos `:hover` | `button:hover` (`estilos.css:430`), `.boton:hover` (`estilos.css:461`), `.boton-eliminar:hover` (`estilos.css:473`) y `.columna:hover .barra` en los gráficos del dashboard (`estilos.css:552`). |

## Reglas nuevas pedidas por el profesor

| Pedido | Evidencia |
|---|---|
| Lista de búsqueda | T2: `listar_socios` (`app.py:572`) valida los cinco estados, busca por nombre o CI con parámetros y escapa los comodines de LIKE. `buscarSocios`, `limpiarBusqueda` y `cargarSocios` (`app.js:205-254`) usan el formulario (`index.html:37`) y muestran "No se encontraron socios". `TestBusqueda` en `tests/test_reglas.py` cubre los filtros sin MySQL. |
| Triggers y auditoría | T4: `copiar_peso_socio` (`base_datos.sql:180`) actualiza el peso; `auditar_plan_socio` (`base_datos.sql:185`) compara plan/vencimiento y registra solo cambios. Migración repetible `migraciones/004_triggers.sql`. La ficha consulta `auditoria` (`app.py:778`) y la muestra con `escaparHtml` (`app.js:747`, `socio.html:160`). Eliminar borra la auditoría dentro de la transacción (`app.py:682`). Congelar/descongelar también se auditan (`app.py:986`, `app.py:1014`). |
| Dashboard | T6: `ver_dashboard` (`app.py:1169`) cuenta socios por estado con `estado_del_socio`, suma los pagos del mes calendario con parámetros y elige el plan más vendido con `elegir_plan_mas_vendido` (`app.py:292`, empate alfabético). Regla 10: `calcular_dias_sin_entrar` y `esta_en_riesgo` (`app.py:274-288`). `cargarDashboard` (`app.js:346`) y `tablaDeSocios` (`app.js:576`) pintan tarjetas y tablas en `dashboard.html`. `graficoDeBarras` (`app.js:485`) dibuja los gráficos con SVG hecho a mano, sin librerías. Pruebas: `TestRiesgo`, `TestPlanMasVendido` y `TestDashboard` en `tests/test_reglas.py`, y `tests/test_dashboard.py` contra MariaDB. |
| Salida y ocupación (agregado) | T10: columna `fecha_hora_salida` (`base_datos.sql:100`) y migración repetible `migraciones/009_salida.sql`. `hacer_salida` (`app.py:878`) cierra la entrada de hoy. Cuenta como adentro quien entró hoy y no salió (`app.py:69`, `app.py:1230`), sobre el `AFORO` (`app.py:50`). En el listado, el botón pasa a **Salida** (`app.js:238`). `medidorOcupacion` (`app.js:435`) muestra la ocupación y el dashboard se actualiza cada 30 segundos (`dashboard.html:98`). Pruebas: `tests/test_ocupacion.py` contra MariaDB. |
| Días sumados en el pago | Regla 7: `calcular_dias_restantes` y `guardar_pago` en `app.py`, tabla `pagos` en `base_datos.sql`, historial en la ficha (`mostrarPagos` en `app.js`). |
| Cancelados | Regla 8: `cancelar_socio` en `app.py`, columna `fecha_cancelacion`, estado calculado en `calcular_estado`. |
| Congelar plan (agregado) | Regla 9: `congelar_plan` y `descongelar_plan` en `app.py`, tabla `congelamientos`. No hace falta una tarea programada, porque el estado sale de comparar fechas. |
| Rutina por día | Reglas 11 y 12: `calcular_siguiente_dia` en el check-in, `armar_seguimiento` y `marcar_ejercicio` en `app.py`, tablas `rutina_ejercicios` y `ejercicios_realizados`, `mostrarSeguimiento` en `app.js`. |
| Asistencia y subir de nivel (agregados) | Reglas 13 y 14: `calcular_asistencia`, `calcular_nivel_sugerido` y `subir_nivel` en `app.py`. |
| Editar manualmente el IMC (opcional) | T9: columna `imc_manual` (`base_datos.sql:85`) y migración repetible `migraciones/008_imc_manual.sql`. `elegir_imc` usa el manual si existe y `categoria_imc` le da la categoría (`app.py:299-321`). `guardar_imc_manual` y `borrar_imc_manual` (`app.py:1282`, `app.py:1299`) son solo de administrador (`solo_admin`). Un peso nuevo (`app.py:1275`) o una altura distinta (`app.py:705`) lo borran. La ficha lo marca como manual y muestra **Volver al IMC calculado** (`app.js:685-689`, `app.js:909`, `app.js:920`, `socio.html:75`). Pruebas: `TestImcManual` en `tests/test_reglas.py` y `tests/test_imc_manual.py` contra MariaDB y MySQL. |
| Login y listado | Regla 15: `exigir_sesion`, `solo_admin` e `iniciar_sesion` en `app.py`, tabla `usuarios`, `login.html` y `usuarios.html`. Las contraseñas se guardan con el hash de Werkzeug. |

## Funcionamiento y conocimiento del sistema (1 pt)

Resumen para explicar en 30 segundos:

1. El navegador carga `index.html` y `app.js` llama a `/api/socios`.
2. Flask recibe la petición, consulta MySQL con `consultar()` y aplica las reglas (estado, IMC, progreso, check-in).
3. Flask devuelve JSON y `app.js` lo pinta en la tabla.

Evidencia de T2: 7 pruebas sin base en `tests/test_reglas.py` y 6 de integración en `tests/test_busqueda.py` en verde sobre MariaDB 11.4.5 aislado (puerto 3310, nunca 3306). Se comprobaron en la app real, con login `admin`, la búsqueda por nombre, por CI, con estado, los cancelados, los comodines como texto y el estado inválido. Los casos para la presentación están en el README, sección "Búsqueda de socios (T2)".

Evidencia T4: 33 pruebas sin base (`tests/test_reglas.py`) y 7 pruebas reales (`tests/test_triggers.py`) en verde sobre MySQL 8.4.5 (3309) y MariaDB 11.4.5 (3308). Cubren copia de peso, cambio de plan/vencimiento, ausencia de cambios, congelar/descongelar, rollback, eliminación y repetición de la migración conservando el historial. Se importaron ambos SQL con los clientes de ambos motores y con phpMyAdmin 5.2.2 (PHP 8.3.20), repitiendo la migración desde su pestaña Importar. Se comprobó la ficha en Chrome a 1280 y 390 píxeles, con login, auditoría llena/vacía y escape de HTML; `node --check static/app.js` también pasó. No se usó el puerto 3306. Pasos y casos de presentación: README, sección "Triggers y auditoría (T4)".

Evidencia de T6: 11 pruebas sin base y 4 de integración (`tests/test_dashboard.py`) en verde sobre MariaDB 11.4.5 aislado (puerto 3310). Se comprobó `dashboard.html` en la app real con login `recepcion`: tarjetas en el orden de la regla 2, socio en riesgo con enlace a su ficha y las cuatro listas. Pasos para la presentación: README, sección "Dashboard (T6)".

Evidencia de T9: 77 pruebas en verde (54 sin base y 23 de integración) sobre MariaDB 11.4.5 (3310) y MySQL 8.4.5 (3311), ambos aislados, incluidas las 6 de `tests/test_imc_manual.py`. `base_datos.sql` y las migraciones 004 y 008, repetidas, se importaron en los dos motores. Se comprobó la ficha de Diego con `admin` (manual, volver al calculado, error fuera de rango) y con `recepcion` (sin controles). Pasos: README, sección "IMC manual (T9)".

Evidencia de T10 (PR #23): 81 pruebas en verde (54 sin base y 27 de integración) sobre un MariaDB aislado (puerto 3307), incluidas las 4 de `tests/test_ocupacion.py`: entrar suma y salir resta, salir sin estar adentro da 400, una entrada de ayer no cuenta y un socio inexistente da 404. Se comprobó en el navegador que la ocupación pasa de 2 a 1 al marcar una salida. Rutas y migración: README, secciones "API" y "Migraciones".

Las reglas del gimnasio están en el README, sección "Reglas del gimnasio".

## Modificación solicitada (5 pts): puntos de cambio

Dónde tocar según lo que pidan:

| Si piden... | Se toca |
|---|---|
| Una regla nueva o distinta (por ejemplo, otros días de aviso de vencimiento) | La función de la regla en `app.py:232-346`, y su prueba en `tests/test_reglas.py`. |
| Otro aforo | La constante `AFORO` en `app.py:50`. |
| Un campo nuevo en el socio | Columna en `base_datos.sql`, `INSERT` y `SELECT` en `app.py`, formulario en `index.html`, dato en `app.js`. |
| Un botón o acción nueva | Ruta en `app.py`, botón en el HTML y función en `app.js` con `llamarApi`. |
| Un cambio visual | Clase nueva en `estilos.css` (por ejemplo, otro `:hover`). |

## Puntos débiles a tener en cuenta

- **Duplicado en el check-in:** la consulta de "ya entró hoy" y la de "últimos 7 días" son dos SQL distintos. Es intencional, porque miden cosas diferentes. Además, el `UNIQUE` de `asistencias` frena dos entradas simultáneas, que la consulta sola no puede detectar.
- **Una sola entrada por día:** por ese mismo `UNIQUE`, quien marca la salida no puede volver a entrar ese día.
