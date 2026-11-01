# Spec: funciones nuevas pedidas por el profesor

El profesor pidió más lógica en el sistema. Este documento fija qué se agrega y con qué reglas. Se divide en 9 tickets, uno por PR, y hay que aprobarlo entre todos antes de empezar a programar.

## Pedido original

- Días sumados en el pago del mes
- Lista de búsqueda
- Login y listado
- Editar manualmente el IMC (opcional)
- Triggers
- Pantalla de vencidos y cancelados, un dashboard
- Rutina por día de cada persona, según los días que vaya: qué hizo y qué no

## Principios

- Se mantiene Flask, MySQL/MariaDB y JavaScript sin framework.
- Las reglas se escriben como funciones cortas en `app.py`, y el frontend solo muestra lo que devuelve la API.
- Todo tiene que poder explicarse al profesor.

## Fuera de alcance

Cobros reales, envío de correos o WhatsApp, códigos QR, portal para socios, librerías de gráficos, varias sedes, IA y CRUD completo de rutinas o ejercicios.

## Por confirmar con el profesor

- **Días sumados:** interpretamos que un pago puede sumar días extra además de los del plan (regla 7). Los valores de 3 días por pago anticipado y 30 días como máximo de promoción son una propuesta nuestra.

## Tickets

| # | Ticket | Depende de |
|---|---|---|
| T1 | Base: validación, transacciones, seguridad y pruebas | Ninguno |
| T2 | Búsqueda de socios | T1 |
| T3 | Precios, pagos y días extra | T1 |
| T4 | Triggers y auditoría | T3 |
| T5 | Cancelar y congelar plan | T3 |
| T6 | Dashboard | T3, T5 |
| T7 | Rutina por día, cumplimiento y nivel | T1 |
| T8 | Login, roles y listado de usuarios | T3, T5, T6, T7 |
| T9 | IMC manual (opcional) | T8 |

## T1. Base

**Validación**
- Los números inválidos (`"abc"`, vacío, negativo) devuelven un error 400 con un mensaje claro, nunca un error 500.
- `objetivo` debe ser `bajar peso`, `ganar musculo` o `mantenerse`.
- `nivel` debe ser `principiante`, `intermedio` o `avanzado`.
- `plan_id` debe ser un entero.
- Un cuerpo JSON vacío o inválido se responde como dato faltante.
- La ficha no se rompe si un socio con datos antiguos no tiene rutina.

**Transacciones**
- Alta, eliminación y registro de peso se confirman o se cancelan enteros.
- Una ayuda en `app.py` comparte la conexión entre las escrituras y hace `rollback` si falla alguna.
- Toda escritura múltiple de los tickets siguientes usa esta misma ayuda.

**Check-in único**
- `asistencias` suma la columna calculada `fecha`, a partir de `fecha_hora`, con `UNIQUE (socio_id, fecha)`.
- Si la base rechaza un duplicado, la API responde "Ya entró hoy".
- La migración elimina primero los duplicados que ya existan, conservando el más antiguo.

**Seguridad y configuración**
- `app.js` escapa todo dato de la base que entra por `innerHTML`.
- `debug` se activa solo con una variable de entorno.

**Pruebas**
- `tests/test_reglas.py` usa `unittest`, sin dependencias nuevas ni base de datos.
- Cubre vencimiento, estado, IMC, progreso y validación, incluidos sus casos límite. Cada ticket siguiente suma las pruebas de sus reglas.

## T2. Búsqueda

- `GET /api/socios?q=texto&estado=Vencido`, con los dos parámetros opcionales y combinables.
- `q` busca coincidencias parciales en nombre y CI con una consulta parametrizada.
- Un `estado` que no existe devuelve 400.
- `index.html` suma un campo de búsqueda, un desplegable de estado y los botones Buscar y Limpiar.
- Sin resultados, la tabla muestra "No se encontraron socios".

## T3. Pagos

**Datos**
- `planes` suma `precio DECIMAL(8,2)`.
- Nueva tabla `pagos`: `socio_id`, `plan_id`, `fecha`, `monto`, `dias_plan`, `dias_anticipo`, `dias_promocion`, `vencimiento_nuevo`.
- El monto se copia del plan, así un cambio de precio no altera los pagos anteriores.
- No se usa símbolo de moneda.

**Regla 7: días extra**

| Situación | Días de anticipo |
|---|---|
| Alta de socio nuevo | 0 |
| Renueva sin haber vencido (incluye el último día) | 3 |
| Renueva con el plan vencido | 0 |

- `dias_promocion` es un entero de 0 a 30 que se escribe a mano.
- Nuevo vencimiento = resultado de la regla 1 + `dias_anticipo` + `dias_promocion`.
- Los días son constantes con nombre en `app.py`, por ejemplo `DIAS_PAGO_ANTICIPADO = 3`.

**API y pantallas**
- `POST /api/socios` y `POST /api/socios/<id>/renovar` registran el pago en la misma transacción que el vencimiento.
- `renovar` acepta `dias_promocion`, y `GET /api/socios/<id>` devuelve el historial de pagos.
- `PUT /api/planes/<id>` cambia el precio, que debe ser mayor que 0.
- La ficha muestra el historial con el desglose de días, e `index.html` suma una sección para editar precios.

## T4. Triggers

**`AFTER INSERT ON registros_peso`**
- Copia el peso nuevo a `socios.peso`.
- Se quita de `registrar_peso` el `UPDATE` que hoy hace ese trabajo.

**`AFTER UPDATE ON socios`**
- Si cambian `plan_id` o `fecha_vencimiento`, inserta una fila en `auditoria_socios`: `socio_id`, plan y vencimiento anteriores y nuevos, y `fecha_hora`.
- La ficha muestra este historial.
- Un trigger no sabe qué usuario de la aplicación hizo el cambio, por lo que la auditoría no lo registra.

**Base de datos**
- Los dos triggers quedan en `base_datos.sql` y en la migración. La migración usa `DROP TRIGGER IF EXISTS` para poder repetirse.

## T5. Cancelar y congelar

**Regla 2 ampliada.** El estado se decide en este orden: Cancelado, Congelado, Vencido, Por vencer, Activo.

**Regla 3 ampliada.** El check-in también se rechaza si el socio está cancelado o congelado.

**Regla 8: cancelar**
- `socios` suma `fecha_cancelacion DATE NULL`. `POST /api/socios/<id>/cancelar` la completa con la fecha de hoy.
- No se puede cancelar a quien ya está cancelado o congelado.
- Se conserva todo su historial. "Eliminar" sigue existiendo aparte, y borra también las filas de las tablas nuevas.
- Renovar reactiva al socio: el plan cuenta desde hoy, sin días de anticipo.
- `GET /api/socios` oculta a los cancelados, salvo con `estado=Cancelado`.

**Regla 9: congelar**
- Nueva tabla `congelamientos`: `socio_id`, `fecha_inicio`, `fecha_fin`.
- `POST /api/socios/<id>/congelar` recibe `dias`, de 1 a 30. Empieza hoy y suma esos días al vencimiento de inmediato, por lo que no hace falta ninguna tarea programada.
- Solo se permite a socios Activos o Por vencer.
- Se permite un congelamiento por período: se rechaza si ya hay uno con `fecha_inicio` igual o posterior a la fecha del último pago.
- El socio está congelado mientras `fecha_inicio <= hoy < fecha_fin`, y deja de estarlo solo al llegar a `fecha_fin`.
- `POST /api/socios/<id>/descongelar` termina antes de tiempo: `fecha_fin` pasa a ser hoy y se restan del vencimiento los días no usados.
- No se puede renovar a un socio congelado.

## T6. Dashboard

- `GET /api/dashboard` y una nueva pantalla `dashboard.html`, enlazada desde `index.html`.
- **Totales:** socios por estado, ingresos del mes calendario y plan más vendido del mes. Si hay empate, gana el primero por orden alfabético.
- **Listas:** vencidos, por vencer, congelados y cancelados, cada uno con enlace a su ficha.
- **Regla 10: socios en riesgo.** Son los Activos o Por vencer cuya última entrada fue hace 14 días o más. Si nunca entraron, se cuenta desde su primer pago; si tampoco tienen pagos, entran en la lista.
- Se muestra con tarjetas y tablas, sin librerías de gráficos.

## T7. Rutina por día

**Datos**
- `rutina_ejercicios`: `rutina_id`, `dia` (1 a 3), `orden`, `nombre`, `series_repeticiones`.
- `asistencias` suma `rutina_id` y `dia_rutina`, que quedan en `NULL` en las entradas antiguas.
- `ejercicios_realizados`: `asistencia_id`, `ejercicio_id`, con `UNIQUE` sobre los dos.
- Los datos de ejemplo incluyen 3 días con 3 ejercicios por día para cada una de las 9 rutinas, 81 filas en total.

**Regla 11: secuencia**
- Cada check-in aceptado guarda la rutina actual del socio y el día siguiente al de su última entrada con esa misma rutina.
- Después del Día 3 vuelve al Día 1. Sin entradas previas con esa rutina, empieza en el Día 1.
- Un check-in rechazado no avanza la secuencia.

**Regla 12: cumplimiento**
- Ventana: últimos 28 días, solo entradas con la rutina actual.
- Cumplimiento = ejercicios realizados / ejercicios asignados, en porcentaje.
- Un ejercicio se puede marcar o desmarcar en cualquier momento, y la API valida que pertenezca a la rutina y al día de esa entrada.

**Regla 13: asistencia**
- % de asistencia = entradas de los últimos 28 días / (días por semana del plan × 4), con un máximo de 100.
- Para los planes libres (7 días) se usa `OBJETIVO_PLAN_LIBRE = 3` como días por semana.
- Es una medida simple: no descuenta socios recién dados de alta ni días congelados.

**Regla 14: sugerencia de nivel**
- Se sugiere subir si hay 8 o más entradas en la ventana, el cumplimiento es de 80% o más, y el nivel no es `avanzado`.
- `POST /api/socios/<id>/subir-nivel` vuelve a comprobar la regla y cambia el nivel. La confirma una persona, nunca es automática.
- Al cambiar de nivel cambia la rutina, así que la secuencia vuelve al Día 1 y la sugerencia desaparece.

**Ficha**
- Muestra el día que le toca, la lista de ejercicios para marcar y el historial por entrada, con lo hecho y lo no hecho.
- También muestra el cumplimiento, el % de asistencia y la sugerencia de nivel, si corresponde.

## T8. Login

**Datos**
- `usuarios`: `nombre`, `usuario` (`UNIQUE`), `clave_hash`, `rol` (`admin` o `recepcion`), `activo`.
- Las contraseñas se guardan con el hash de Werkzeug, que ya viene con Flask.
- Los datos de ejemplo traen un usuario por rol. Sus claves son de prueba y se documentan en el README.

**Regla 15: acceso**
- `POST /api/login`, `POST /api/logout` y `GET /api/sesion`.
- Toda ruta `/api/*`, salvo el login, responde 401 sin sesión. Con sesión pero sin el rol necesario responde 403.
- Un mismo mensaje cubre usuario inexistente, clave incorrecta y usuario desactivado.
- `llamarApi` redirige a `login.html` al recibir un 401.
- La cookie de sesión usa `HttpOnly` y `SameSite=Lax`.
- La clave de sesión sale de una variable de entorno. Si falta, se genera una al azar al arrancar, con lo que las sesiones se pierden al reiniciar.

**Permisos**

| Acción | Administrador | Recepción |
|---|---|---|
| Altas, check-in, pesos, rutinas, renovar, cancelar y congelar | Sí | Sí |
| Ver dashboard | Sí | Sí |
| Días de promoción mayores que 0 | Sí | No |
| Editar precios de planes | Sí | No |
| Eliminar socios | Sí | No |
| Ver, crear, activar y desactivar usuarios | Sí | No |

- Un administrador no puede desactivarse a sí mismo.
- Las pantallas ocultan lo que el rol no permite, pero quien lo hace cumplir es la API.

## T9. IMC manual (opcional)

- `socios` suma `imc_manual DECIMAL(4,2) NULL`. Solo lo edita el administrador, con valores de 10 a 70.
- Si tiene valor, reemplaza al calculado: la categoría sale de ese número y la ficha lo indica como "manual".
- Registrar un peso nuevo o cambiar la altura lo borra, para que no quede desactualizado. También hay un botón para volver al cálculo.

## Definición de terminado (cada ticket)

- Un PR con su rama, revisado y fusionado por el grupo.
- Pruebas de las reglas nuevas, en verde.
- Si cambia la base: `base_datos.sql` actualizado, una migración numerada en `migraciones/` y datos de ejemplo para probar cada caso.
- `README.md` e `INDICADORES.md` actualizados, con reglas, rutas y evidencia para la presentación.
- Probado en la app contra MySQL. Si algo no se pudo probar, el PR lo dice.
