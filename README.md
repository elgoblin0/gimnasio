# Sistema de gimnasio

Proyecto de la facultad: gestión de socios de un gimnasio. Permite dar de alta socios, registrar sus entradas (check-in), renovar planes, registrar sus pagos y seguir su peso, IMC y rutina. Se entra con usuario y contraseña, con permisos según el rol.

**Stack:** XAMPP (MySQL/MariaDB) + Python Flask (backend) + JavaScript (frontend).

## Dos versiones del proyecto

- **Estándar:** https://github.com/elgoblin0/gimnasio — mantiene Flask, MySQL y JavaScript, con mejoras pequeñas y explicables.
- **Pro:** https://github.com/elgoblin0/gimnasio-pro — desarrollo independiente para explorar una experiencia de producto completa.
- La etiqueta `base-original` conserva el punto de partida compartido.
- Cada repositorio tiene su propia rama `main`. No se sincronizan automáticamente: los arreglos compartidos se trasladan de forma selectiva.
- Ver `ROADMAP.md` para el alcance y las próximas etapas de esta versión.

## Reglas del proyecto

1. Siempre lo más sencillo posible, para poder explicar el código al profesor.
2. Antes de escribir código, todo el grupo tiene que estar 100% de acuerdo.

## Qué hace falta instalar

- [XAMPP](https://www.apachefriends.org/es/index.html): trae MySQL y phpMyAdmin.
- [Python 3](https://www.python.org/downloads/). En Windows, marcar **"Add Python to PATH"** al instalarlo.
- [Git](https://git-scm.com/downloads).

## Cómo ponerlo en marcha

1. Descargar el proyecto (solo la primera vez):
   ```
   git clone https://github.com/elgoblin0/gimnasio.git
   cd gimnasio
   ```
2. Abrir el panel de XAMPP y arrancar **MySQL** y **Apache** (Apache solo hace falta para phpMyAdmin).
3. Abrir `http://localhost/phpmyadmin`, ir a la pestaña **Importar** y subir `base_datos.sql`.
   (Ojo: borra la base de datos `gimnasio` y la vuelve a crear con los datos de ejemplo. Usa un servidor exclusivo para este proyecto; no importes este archivo en una instancia compartida.)
4. Instalar las librerías de Python:
   ```
   pip3 install -r requirements.txt
   ```
5. Arrancar el servidor:
   ```
   python3 app.py
   ```
6. Abrir `http://localhost:5001` en el navegador y entrar con un usuario de ejemplo:

   | Usuario | Contraseña | Rol |
   |---|---|---|
   | `admin` | `admin1234` | Administrador |
   | `recepcion` | `recepcion1234` | Recepción |

   Estas claves son solo de prueba y están en el repositorio: no se usan fuera de este proyecto.

> En Windows puede que los comandos sean `pip` y `python` en vez de `pip3` y `python3`.

Para parar el servidor: `Ctrl + C` en la terminal.

Para programar con recarga automática y mensajes de error detallados, arranca el servidor con la variable de entorno `GIMNASIO_DEBUG=1`. Sin ella, el modo debug queda apagado.

Las sesiones se firman con la variable de entorno `GIMNASIO_SECRET_KEY`. Si no está, se genera una clave al azar al arrancar, y al reiniciar el servidor hay que volver a entrar. Nunca se sube al repositorio.

## Pruebas

Comprueban las reglas y las validaciones. No necesitan MySQL ni instalar nada más:

```
python3 -m unittest tests.test_reglas
```

## Búsqueda de socios (T2)

En la lista, escribe parte del nombre o del CI, elige un estado si quieres y pulsa **Buscar** (también funciona Enter). **Limpiar** vacía ambos filtros y vuelve a mostrar la lista sin cancelados. Si no hay coincidencias, aparece "No se encontraron socios".

- `GET /api/socios` admite `q` y `estado`, opcionales y combinables; requiere sesión tanto para administrador como para recepción.
- `q` busca coincidencias parciales en nombre o CI. Se recortan los espacios de los extremos; vacío equivale a no buscar. `%` y `_` se buscan como texto, no como comodines.
- Los estados válidos son `Activo`, `Por vencer`, `Vencido`, `Congelado` y `Cancelado`. Cualquier otro valor (incluido `estado=`) devuelve 400.
- Sin `estado` se ocultan los cancelados. Un estado explícito muestra solo ese estado, conservando la prioridad de cancelación y congelamiento.
- La consulta usa parámetros `%s` y `LIKE ... ESCAPE '!'`; el estado se filtra con `estado_del_socio`, sin duplicar las reglas en SQL. No cambia la base ni necesita migración.

Para demostrarlo con los datos de ejemplo, inicia sesión y prueba `q=Gomez` (Javier y Maria), `q=Gomez&estado=Vencido` (Maria), `q=9999` (Valentina, por su CI), `estado=Congelado` (Martin) y `estado=Cancelado` (Paula). Prueba un texto inexistente para ver el mensaje vacío y luego **Limpiar**. En la API, `estado=Inventado` debe devolver 400; buscar `%` o `_` no debe traer a todos los socios.

Evidencia T2: 7 pruebas sin base en `tests/test_reglas.py` (sesión y consultas simuladas) y 6 de integración en `tests/test_busqueda.py` sobre MariaDB 11.4.5 en un servidor aislado (puerto 3310, nunca 3306): coincidencia parcial sin distinguir mayúsculas, CI parcial, texto + estado, cancelados ocultos, `%`, `_` y `!` como texto, intento de inyección y estado inválido. También se comprobaron en la app real, con login `admin`, los casos de demostración de arriba. Se ejecutan igual que las de T4, con `GIMNASIO_TEST_PORT`.

## Archivos

```
gimnasio/
├── base_datos.sql     ← tablas y datos de ejemplo
├── app.py             ← backend Flask: reglas + API
├── requirements.txt   ← librerías de Python
├── migraciones/       ← cambios para una base ya creada
├── tests/             ← pruebas de las reglas
└── static/
    ├── login.html     ← entrada al sistema
    ├── index.html     ← búsqueda de socios, entrada/salida y alta
    ├── socio.html     ← ficha en pestañas: resumen, rutina, progreso y pagos, editar y eliminar
    ├── dashboard.html ← ocupación ahora, gráficos, socios en riesgo y listas por estado
    ├── planes.html    ← precios de los planes (solo administrador)
    ├── usuarios.html  ← listado y alta de usuarios (solo administrador)
    ├── app.js         ← llamadas a la API (fetch)
    └── estilos.css
```

## Base de datos

| Tabla | Qué guarda |
|---|---|
| `usuarios` | Quienes entran al sistema: usuario, contraseña con hash, rol y si está activo. |
| `planes` | Nombre, duración en días, cuántos días por semana se puede entrar (7 = libre) y precio. |
| `rutinas` | Una rutina por cada combinación de objetivo + nivel. |
| `rutina_ejercicios` | Los ejercicios de cada rutina: 3 días con 3 ejercicios cada uno. |
| `socios` | Datos del socio, su plan y la fecha de vencimiento. |
| `asistencias` | Una fila por cada entrada al gimnasio, con la rutina y el día que le tocaron. |
| `ejercicios_realizados` | Qué ejercicios hizo el socio en cada entrada. |
| `registros_peso` | Historial de peso para ver el progreso. |
| `pagos` | Una fila por cada pago: monto, días del plan y días que le quedaban al socio. |
| `congelamientos` | Una fila por cada vez que un socio congela su plan, con su inicio y su fin. |
| `auditoria_socios` | Plan y vencimiento anteriores y nuevos, socio y fecha/hora de cada cambio. |

## Reglas del gimnasio (la lógica que se evalúa)

Las reglas están en `app.py`. Los dos triggers de T4 están en `base_datos.sql` y en `migraciones/004_triggers.sql`.

| # | Regla |
|---|---|
| 1 | Al dar de alta o renovar se calcula el vencimiento. Si sigue activo, se suma a lo que le queda; si no, desde hoy. |
| 2 | Estado del socio, en este orden: Cancelado / Congelado / Vencido / Por vencer (7 días o menos) / Activo. |
| 3 | Check-in: se rechaza si el socio está cancelado o congelado, si el plan está vencido, si ya entró hoy o si ya usó sus días por semana (últimos 7 días). La base de datos también impide dos entradas el mismo día. |
| 4 | IMC = peso / altura², con su categoría. Si el administrador cargó un IMC manual, se usa ese (T9). |
| 5 | Rutina asignada según objetivo + nivel. |
| 6 | Progreso: primer peso vs último según el objetivo (mantenerse = 2 kg o menos de diferencia). |
| 7 | Días extra: quien paga antes de vencer recibe los días del plan más los que le quedaban (5 restantes + plan de 30 = vence en 35 días). Cada pago registra ese desglose. |
| 8 | Cancelar: conserva el historial y oculta al socio de la lista. Si renueva, vuelve con el plan contado desde hoy, sin los días que le quedaban. |
| 9 | Congelar: de 1 a 30 días, una vez por período, solo con el plan en uso. Los días se suman al vencimiento de inmediato. Si vuelve antes, se restan los no usados. |
| 10 | Socios en riesgo: Activos o Por vencer cuya última entrada fue hace 14 días o más. Si nunca entraron, se cuenta desde su primer pago; sin entradas ni pagos, también están en riesgo. Los congelados nunca lo están. |
| 11 | Rutina en secuencia: cada check-in aceptado pasa al día siguiente de su rutina, y después del Día 3 vuelve al Día 1. Si cambia de rutina, empieza en el Día 1. |
| 12 | Cumplimiento: ejercicios hechos / asignados en los últimos 28 días, solo con la rutina actual. |
| 13 | Asistencia: entradas de los últimos 28 días / (días por semana × 4), con un máximo de 100%. Un plan libre cuenta como 3 días por semana. |
| 14 | Subir de nivel: se sugiere con 8 entradas o más en 28 días y 80% o más de cumplimiento, salvo en avanzado. Lo confirma una persona. |
| 15 | Acceso: sin sesión, la API responde 401. Recepción no puede eliminar socios, cambiar precios, cargar el IMC manual ni gestionar usuarios, y la API responde 403. Un administrador no puede desactivarse a sí mismo. |

## Cómo probar las reglas con los datos de ejemplo

Las fechas de ejemplo se calculan a partir del día en que se importa el `.sql`, así que siempre hay un socio en cada estado.

| Socio | Qué se puede probar |
|---|---|
| Ana Lopez | Activa. El check-in funciona. Va bien bajando de peso (72 → 68 kg). En sus pagos se ve una renovación con 5 días restantes. Con 8 entradas y 100% de cumplimiento, se le sugiere subir de nivel. |
| Carlos Ruiz | Por vencer (5 días). Plan de 3 días/semana y ya entró 2 veces: el primer check-in funciona, el segundo dice "Ya entró hoy". Hizo parte de su rutina: 67% de cumplimiento. |
| Maria Gomez | Vencida. El check-in se rechaza. Al renovar, el plan cuenta desde hoy. |
| Luis Fernandez | Activo (plan anual). Quiere bajar peso pero subió (88 → 90 kg): "No va bien". Nunca entró y pagó hace 165 días: aparece en riesgo en el dashboard. |
| Diego Pereira | Activo. Quiere mantenerse y se movió 1 kg (80 → 81): "Va bien". Tiene un IMC manual de 24.80 (Normal); el calculado da Sobrepeso. |
| Lucia Rodriguez | Por vencer (2 días). Bajó de 95 a 91 kg: "Va bien". IMC en Obesidad. |
| Valentina Diaz | Vencida. Quiere mantenerse pero subió 4 kg (48 → 52): "No va bien". IMC en Bajo peso. |
| Javier Gomez | Plan de 3 días/semana y ya entró 3 veces en los últimos 7 días: el check-in dice "Ya usó sus 3 días de los últimos 7". |
| Paula Sosa | Cancelada (se ve eligiendo "Cancelado" en el filtro de estado). Al renovar, el plan cuenta desde hoy, sin sus 10 días restantes. |
| Martin Silva | Congelado 12 días más. El check-in se rechaza, y al descongelar se restan esos 12 días. |

Si los datos quedan desordenados de tanto probar, se puede volver a importar `base_datos.sql` en el servidor exclusivo del proyecto; se pierden los datos de esa base.

### Migraciones

Si ya tenías la base creada y no quieres perder los datos, en vez de reimportar `base_datos.sql` importa (en phpMyAdmin, pestaña **Importar**) el archivo de `migraciones/` que corresponda:

| Archivo | Qué hace |
|---|---|
| `migraciones/001_dni_a_ci.sql` | Renombra la columna `socios.dni` a `ci` conservando los datos. Se puede repetir sin problema. |
| `migraciones/002_checkin_unico.sql` | Impide dos entradas del mismo socio el mismo día. Si ya hay duplicados, conserva la entrada más antigua y borra las demás. Se puede repetir sin problema. |
| `migraciones/003_pagos.sql` | Agrega el precio de los planes y la tabla de pagos. Se puede repetir sin problema. |
| `migraciones/004_triggers.sql` | Crea la auditoría y los dos triggers. Conserva los datos al repetirse con `DROP TRIGGER IF EXISTS`; no reconstruye cambios anteriores. |
| `migraciones/005_cancelar_congelar.sql` | Agrega la fecha de cancelación y la tabla de congelamientos. Se puede repetir sin problema. |
| `migraciones/006_rutina_por_dia.sql` | Agrega los ejercicios por día y lo que hizo cada socio. Las entradas anteriores quedan sin rutina. Se puede repetir sin problema. |
| `migraciones/007_usuarios.sql` | Agrega los usuarios, con los dos de ejemplo. Se puede repetir sin problema. |
| `migraciones/008_imc_manual.sql` | Agrega `socios.imc_manual`, vacío para todos los socios. Se puede repetir sin problema. |
| `migraciones/009_salida.sql` | Agrega `asistencias.fecha_hora_salida` (T10). Las entradas viejas quedan sin salida y no cuentan como adentro. Se puede repetir sin problema. |

## Dashboard (T6)

El enlace **Dashboard** de la página principal abre `dashboard.html`. Lo ven el administrador y recepción.

- **Socios por estado:** una tarjeta por estado, con la regla 2 (`estado_del_socio`), sin duplicarla en SQL.
- **Este mes:** ingresos (suma de `pagos.monto`) y plan más vendido (más pagos) del mes calendario, del día 1 al último día. Si dos planes empatan, gana el primero por orden alfabético (`elegir_plan_mas_vendido`). Sin pagos en el mes muestra 0.00 y "Sin ventas".
- **Socios en riesgo (regla 10):** `calcular_dias_sin_entrar` cuenta desde la última entrada o, si nunca entró, desde el primer pago; `esta_en_riesgo` exige estado Activo o Por vencer y 14 días o más (`DIAS_PARA_RIESGO`). Sin entradas ni pagos aparece como "Sin datos".
- **Listas:** vencidos, por vencer, congelados y cancelados, cada uno con su botón **Ver ficha**.
- Solo tarjetas y tablas con CSS: no usa librerías de gráficos. No cambia la base ni necesita migración.

Para la presentación: con los datos de ejemplo hay 4 activos, 2 por vencer, 2 vencidos, 1 congelado (Martin) y 1 cancelado (Paula), y Luis Fernandez aparece en riesgo. Como las fechas de ejemplo son relativas al día de importación, los ingresos del mes dependen de la fecha: renueva a cualquier socio y recarga el dashboard para ver subir los ingresos y cambiar el plan más vendido. Congela a Luis y desaparece de la lista de riesgo.

Evidencia T6: 11 pruebas sin base en `tests/test_reglas.py` (regla 10 en sus límites, empate del plan más vendido, mes sin ventas y la ruta completa con datos simulados) y 4 de integración en `tests/test_dashboard.py` sobre MariaDB 11.4.5 aislado (puerto 3310): entradas de hace 13 y 14 días, socio que nunca entró, congelado, cancelado, ingresos del mes y pago del mes anterior, y acceso de recepción. También se comprobó la pantalla en la app real con login `recepcion`.

## IMC manual (T9)

- `socios.imc_manual DECIMAL(4,2) NULL`. Si tiene valor, reemplaza al IMC calculado: la categoría sale de ese número (`elegir_imc` y `categoria_imc`, regla 4) y la ficha lo muestra como "- manual".
- Solo el administrador lo guarda (`PUT /api/socios/<id>/imc`, de 10 a 70) o vuelve al calculado (`DELETE /api/socios/<id>/imc`, botón **Volver al IMC calculado**). Recepción recibe 403 y no ve esos controles.
- Registrar un peso nuevo lo borra en la misma transacción que el peso. Editar el socio lo borra solo si cambia la altura (comparada con 2 decimales, como la guarda la base).
- Para una base existente, importa `migraciones/008_imc_manual.sql`.

Para la presentación, inicia sesión como `admin` y abre la ficha de Diego Pereira: muestra 24.8 (Normal) - manual. **Volver al IMC calculado** muestra 25.56 (Sobrepeso). Guarda 24.8 otra vez y registra un peso: vuelve al calculado. Con `recepcion` no aparecen los controles y la API responde 403.

Evidencia T9: 3 pruebas sin base en `tests/test_reglas.py` (manual contra calculado y límites 10/70) más las rutas de admin en `TestPermisos`, y 6 de integración en `tests/test_imc_manual.py`: guardar, fuera de rango, 403 de recepción, peso nuevo, cambio de altura y volver al calculado. Las 77 pruebas pasan sobre MariaDB 11.4.5 (puerto 3310) y MySQL 8.4.5 (puerto 3311), ambos aislados. `base_datos.sql` y las migraciones 004 y 008 (repetidas) se importaron en los dos motores con su cliente SQL. Se comprobó la ficha en la app real con los dos roles. No se usó el puerto 3306.

## Triggers y auditoría (T4)

- `copiar_peso_socio`, `AFTER INSERT ON registros_peso`: copia cada peso insertado a `socios.peso`, incluso si se inserta desde SQL. `registrar_peso` solo inserta el registro; el trigger participa en la misma transacción.
- `auditar_plan_socio`, `AFTER UPDATE ON socios`: inserta en `auditoria_socios` solo si cambia `plan_id` o `fecha_vencimiento`. `<=>` compara los valores de forma segura; `NOT` detecta una diferencia. Cambiar peso, nombre o guardar el mismo plan y vencimiento no agrega auditoría.
- Renovar, congelar y descongelar quedan registrados porque cambian el vencimiento. El trigger no conoce al usuario de la aplicación, así que no se guarda ese dato.
- `GET /api/socios/<id>` devuelve `auditoria`, del cambio más reciente al más antiguo (fecha/hora e id). Cada fila incluye `plan_anterior`, `plan_nuevo`, `nombre_plan_anterior`, `nombre_plan_nuevo`, `vencimiento_anterior`, `vencimiento_nuevo` y `fecha_hora` en texto. Los nombres se consultan del catálogo actual de planes.
- La ficha muestra **Historial de plan y vencimiento**, o “Sin cambios de plan o vencimiento”. Todos sus valores pasan por `escaparHtml` antes de entrar por `innerHTML`.
- Para una base existente, importa `migraciones/004_triggers.sql` antes de usar esta versión de la app. Requiere las tablas `socios`, `planes` y `registros_peso`; se conserva el historial al repetirla. Cada trigger tiene una sola sentencia SQL, sin `DELIMITER`, para importar desde phpMyAdmin en MySQL o MariaDB.

Para la presentación, inicia sesión como `admin`. Ana ya tiene una renovación histórica y Martin un congelamiento histórico en los datos de ejemplo; Carlos empieza sin auditoría. En la ficha de Carlos:

1. Registra un peso: cambia el peso actual, pero la auditoría sigue vacía.
2. Renueva con otro plan: aparece una fila con los dos planes y vencimientos.
3. Congela 7 días: aparece otra fila y el vencimiento aumenta 7 días.
4. Descongela el mismo día: aparece otra fila y el vencimiento vuelve al anterior.
5. Edita solo el teléfono o nombre: no aparece una fila nueva. Eliminar el socio borra también la auditoría.

Pruebas de integración reproducibles, sin dependencias nuevas: prepara una base de ejemplo en un servidor **aislado**, configura su puerto y ejecuta (PowerShell):

```powershell
$env:GIMNASIO_TEST_PORT = "3309"
python -m unittest tests.test_reglas tests.test_triggers tests.test_busqueda tests.test_dashboard tests.test_imc_manual -v
```

`tests/test_triggers.py` no importa `base_datos.sql` ni borra la base; rechaza el puerto 3306, inicia sesión con `admin` y crea/elimina sus propios socios. Sin la variable, las 7 pruebas de integración se omiten. La prueba de repetición reemplaza los triggers, así que requiere una instancia exclusiva y permiso `TRIGGER`.

Evidencia T4: 33 pruebas sin base y 7 de integración en verde con MySQL 8.4.5 (3309) y MariaDB 11.4.5 (3308). Se importó `base_datos.sql` y la migración repetida en ambos mediante sus clientes SQL y desde la pestaña Importar de phpMyAdmin 5.2.2 (PHP 8.3.20). También se comprobó la actualización desde la base de `main` anterior a T4. Se comprobaron peso directo y por API, cambios de plan/vencimiento, ausencia de auditoría sin cambios, congelar/descongelar, rollback, eliminación e historial conservado al repetir la migración. Chrome sin interfaz verificó login real, historial con datos y vacío, escape de HTML y la ficha a 1280 y 390 píxeles, sin errores JavaScript. No se utilizó el puerto 3306.

## API (lo que llama `app.js`)

Toda ruta pide sesión, salvo el login. Las marcadas con (admin) son solo para el administrador.

| Método | Ruta | Qué hace |
|---|---|---|
| POST | `/api/login` | Iniciar sesión |
| POST | `/api/logout` | Cerrar sesión |
| GET | `/api/sesion` | Quién tiene la sesión abierta |
| GET | `/api/usuarios` | Listado de usuarios (admin) |
| POST | `/api/usuarios` | Crear un usuario (admin) |
| PATCH | `/api/usuarios/<id>` | Activar o desactivar un usuario (admin) |
| GET | `/api/planes` | Lista de planes |
| PUT | `/api/planes/<id>` | Cambiar el precio de un plan (admin) |
| GET | `/api/socios` | Busca por `?q=texto&estado=Vencido` (opcionales y combinables). Sin estado, oculta cancelados; con `estado=Cancelado`, muestra solo cancelados |
| POST | `/api/socios` | Alta de socio |
| GET | `/api/socios/<id>` | Ficha completa (IMC, indicando si es manual, rutina, progreso, historial, pagos, auditoría) |
| PUT | `/api/socios/<id>` | Editar nombre, CI, teléfono, altura, objetivo y nivel |
| DELETE | `/api/socios/<id>` | Eliminar socio y sus historiales, incluida la auditoría, en una transacción (admin) |
| POST | `/api/socios/<id>/checkin` | Registrar una entrada |
| POST | `/api/socios/<id>/salida` | Registrar la salida de hoy (T10) |
| POST | `/api/socios/<id>/renovar` | Renovar o cambiar de plan, registrando el pago |
| POST | `/api/socios/<id>/peso` | Registrar un peso nuevo (borra el IMC manual) |
| PUT | `/api/socios/<id>/imc` | Guardar un IMC manual de 10 a 70 (admin) |
| DELETE | `/api/socios/<id>/imc` | Volver al IMC calculado (admin) |
| POST | `/api/socios/<id>/cancelar` | Cancelar un socio |
| POST | `/api/socios/<id>/congelar` | Congelar el plan unos días |
| POST | `/api/socios/<id>/descongelar` | Terminar el congelamiento antes de tiempo |
| POST, DELETE | `/api/socios/<id>/asistencias/<id>/ejercicios/<id>` | Marcar o desmarcar un ejercicio de una entrada |
| POST | `/api/socios/<id>/subir-nivel` | Confirmar la subida de nivel sugerida |
| GET | `/api/dashboard` | Socios por estado, ingresos y plan más vendido del mes, listas por estado, socios en riesgo, ingresos de los últimos 6 meses, entradas de los últimos 28 días y personas adentro sobre el aforo |

## Problemas frecuentes

- **`Can't connect to MySQL server`**: MySQL no está arrancado en XAMPP.
- **`Unknown database 'gimnasio'`**: falta importar `base_datos.sql` en phpMyAdmin.
- **`Access denied for user 'root'`**: tu MySQL tiene contraseña. Ponla en `password=""` dentro de `conectar()` en `app.py`, pero **no la subas a GitHub**.
- **`ModuleNotFoundError: No module named 'flask'`**: falta el paso 4 (`pip3 install -r requirements.txt`).
- **`Address already in use`**: el servidor ya está abierto en otra terminal. Ciérralo con `Ctrl + C`.

## Comandos básicos de git

```
git pull                      # traer los cambios de los compañeros (¡siempre antes de empezar!)
git add .                     # preparar mis cambios
git commit -m "qué he hecho"  # guardarlos con un mensaje
git push                      # subirlos a GitHub
```

Si `git push` da error porque alguien subió cambios antes, haz `git pull` y vuelve a hacer `git push`.
