# =============================================
# Backend del sistema de gimnasio (Flask + MySQL)
# Ejecutar con: python3 app.py
# Abrir en el navegador: http://localhost:5001
# =============================================

import math
import os
import secrets
from contextlib import contextmanager
from datetime import date, timedelta
from functools import wraps

import mysql.connector
from flask import Flask, g, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

# static_url_path="" hace que los archivos de static/ se sirvan desde la raíz
# (ej: http://localhost:5001/socio.html)
app = Flask(__name__, static_folder="static", static_url_path="")

# La clave firma la cookie de sesión. Si no está la variable de entorno, se genera
# una al azar al arrancar: nunca queda en el repositorio, pero las sesiones se pierden al reiniciar.
app.secret_key = os.environ.get("GIMNASIO_SECRET_KEY") or secrets.token_hex(32)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Usuarios (REGLA 15)
ROLES = ("admin", "recepcion")
CLAVE_MINIMA = 8
LARGO_MAXIMO_USUARIO = {"nombre": 100, "usuario": 50}

# Valores permitidos y límites de los datos de un socio
OBJETIVOS = ("bajar peso", "ganar musculo", "mantenerse")
NIVELES = ("principiante", "intermedio", "avanzado")
LARGO_MAXIMO = {"nombre": 100, "ci": 20, "telefono": 20}
ALTURA_MINIMA = 0.5
ALTURA_MAXIMA = 2.5
PESO_MINIMO = 1
PESO_MAXIMO = 500
PRECIO_MINIMO = 0.01
PRECIO_MAXIMO = 999999.99
CONGELAMIENTO_MAXIMO = 30

# Rutina por día (REGLAS 11 a 14)
DIAS_POR_RUTINA = 3
VENTANA_DIAS = 28
OBJETIVO_PLAN_LIBRE = 3  # días por semana que se esperan de un plan libre
ENTRADAS_PARA_SUBIR = 8
CUMPLIMIENTO_PARA_SUBIR = 80

# Columna calculada: 1 si hoy el socio está dentro de un congelamiento (REGLA 9)
SQL_CONGELADO = (
    "EXISTS(SELECT 1 FROM congelamientos c WHERE c.socio_id = s.id "
    "AND c.fecha_inicio <= CURDATE() AND CURDATE() < c.fecha_fin) AS congelado"
)


# ---------------------------------------------
# CONEXIÓN A LA BASE DE DATOS
# ---------------------------------------------

def conectar():
    # Datos por defecto de XAMPP: usuario root sin contraseña
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="gimnasio",
        use_pure=True,  # conector en Python puro (más fácil de instalar)
    )


def consultar(sql, parametros=()):
    # Ejecuta un SELECT y devuelve una lista de diccionarios
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute(sql, parametros)
    filas = cursor.fetchall()
    conexion.close()
    return filas


def consultar_uno(sql, parametros=()):
    # Igual que consultar(), pero devuelve solo la primera fila (o None)
    filas = consultar(sql, parametros)
    if len(filas) == 0:
        return None
    return filas[0]


def ejecutar(sql, parametros=()):
    # Ejecuta un INSERT o UPDATE y devuelve el id de la fila nueva
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute(sql, parametros)
    conexion.commit()
    nuevo_id = cursor.lastrowid
    conexion.close()
    return nuevo_id


@contextmanager
def transaccion():
    # Las escrituras del bloque "with" se confirman juntas.
    # Si una falla, se deshacen todas (rollback).
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        yield cursor
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def error(mensaje, codigo=400):
    # Respuesta de error que muestra el frontend
    return jsonify({"error": mensaje}), codigo


def socio_existe(socio_id):
    return consultar_uno("SELECT id FROM socios WHERE id = %s", (socio_id,)) is not None


# Devuelve los datos necesarios para calcular el estado del socio (o None)
def buscar_socio(socio_id):
    return consultar_uno(
        "SELECT s.id, s.fecha_vencimiento, s.fecha_cancelacion, " + SQL_CONGELADO +
        " FROM socios s WHERE s.id = %s",
        (socio_id,),
    )


def leer_json():
    # Devuelve el JSON del pedido. Un cuerpo vacío o inválido cuenta como datos faltantes.
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        return {}
    return datos


def leer_numero(valor):
    # Devuelve el número, o None si no es válido (ej: "abc", vacío, "nan")
    if isinstance(valor, bool):
        return None
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numero):
        return None
    return numero


def leer_entero(valor):
    # Igual que leer_numero(), pero solo acepta números enteros
    numero = leer_numero(valor)
    if numero is None or numero != int(numero):
        return None
    return int(numero)


def validar_peso(valor):
    # Devuelve el mensaje de error, o None si el peso está bien
    peso = leer_numero(valor)
    if peso is None or peso < PESO_MINIMO or peso > PESO_MAXIMO:
        return "El peso debe estar entre " + str(PESO_MINIMO) + " y " + str(PESO_MAXIMO) + " kg"
    return None


# Revisa los campos obligatorios y sus valores (se usa al crear y al editar).
# Devuelve el mensaje de error, o None si todo está bien.
def validar_datos_socio(datos, obligatorios):
    for campo in obligatorios:
        valor = datos.get(campo)
        if valor is None or str(valor).strip() == "":
            return "Falta el campo: " + campo

    for campo, largo in LARGO_MAXIMO.items():
        valor = datos.get(campo)
        if valor is None:
            continue
        if not isinstance(valor, str):
            return "El campo " + campo + " debe ser texto"
        if len(valor) > largo:
            return "El campo " + campo + " admite hasta " + str(largo) + " caracteres"

    if datos["objetivo"] not in OBJETIVOS:
        return "El objetivo no es válido"
    if datos["nivel"] not in NIVELES:
        return "El nivel no es válido"

    altura = leer_numero(datos["altura"])
    if altura is None or altura < ALTURA_MINIMA or altura > ALTURA_MAXIMA:
        return "La altura debe estar en metros (ej: 1.75)"

    if "peso" in obligatorios:
        mensaje = validar_peso(datos["peso"])
        if mensaje:
            return mensaje

    if "plan_id" in obligatorios and leer_entero(datos["plan_id"]) is None:
        return "El plan no es válido"

    return None


# ---------------------------------------------
# REGLAS DEL GIMNASIO
# ---------------------------------------------

# REGLA 1: calcular la nueva fecha de vencimiento
# Si el socio sigue activo, los días se suman a su vencimiento actual.
# Si es nuevo (None) o ya venció, se suman a partir de hoy.
def calcular_vencimiento(fecha_vencimiento, dias):
    hoy = date.today()
    if fecha_vencimiento is not None and fecha_vencimiento >= hoy:
        return fecha_vencimiento + timedelta(days=dias)
    return hoy + timedelta(days=dias)


# REGLA 7: días que le quedaban al socio al pagar (sus "días extra")
# El último día, o con el plan vencido, ya no le queda ninguno.
def calcular_dias_restantes(fecha_vencimiento):
    if fecha_vencimiento is None or fecha_vencimiento < date.today():
        return 0
    return (fecha_vencimiento - date.today()).days


# REGLA 2: estado del socio
# Primero cancelado y congelado; si no, según los días que le quedan.
def calcular_estado(fecha_vencimiento, fecha_cancelacion=None, congelado=False):
    if fecha_cancelacion is not None:
        return "Cancelado"
    if congelado:
        return "Congelado"
    dias_restantes = (fecha_vencimiento - date.today()).days
    if dias_restantes < 0:
        return "Vencido"
    if dias_restantes <= 7:
        return "Por vencer"
    return "Activo"


# Estado de una fila de socio que trae fecha_cancelacion y congelado (SQL_CONGELADO)
def estado_del_socio(socio):
    return calcular_estado(socio["fecha_vencimiento"], socio["fecha_cancelacion"], socio["congelado"])


# REGLA 9: días de un congelamiento que todavía no se usaron
def calcular_dias_no_usados(fecha_fin):
    return max((fecha_fin - date.today()).days, 0)


# REGLA 4: IMC = peso / altura² y su categoría
def calcular_imc(peso, altura):
    imc = peso / (altura * altura)
    if imc < 18.5:
        categoria = "Bajo peso"
    elif imc < 25:
        categoria = "Normal"
    elif imc < 30:
        categoria = "Sobrepeso"
    else:
        categoria = "Obesidad"
    return round(imc, 2), categoria  # se redondea al final para no cambiar la categoría


# REGLA 6: comparar el primer peso con el último según el objetivo
def calcular_progreso(objetivo, peso_inicial, peso_actual):
    diferencia = round(peso_actual - peso_inicial, 1)
    if objetivo == "bajar peso":
        va_bien = diferencia < 0
    elif objetivo == "ganar musculo":
        va_bien = diferencia > 0
    else:  # mantenerse: no moverse más de 2 kg
        va_bien = abs(diferencia) <= 2

    if va_bien:
        resultado = "Va bien"
    else:
        resultado = "No va bien"
    return diferencia, resultado


# REGLA 11: día de rutina que sigue al último que hizo
# Sin entradas previas con esa rutina empieza en el Día 1. Después del último, vuelve al 1.
def calcular_siguiente_dia(ultimo_dia):
    if ultimo_dia is None or ultimo_dia >= DIAS_POR_RUTINA:
        return 1
    return ultimo_dia + 1


# REGLA 12: porcentaje de ejercicios hechos sobre los asignados
def calcular_cumplimiento(realizados, asignados):
    if asignados == 0:
        return 0
    return round(100 * realizados / asignados)


# REGLA 13: entradas de la ventana contra las esperadas según el plan (máximo 100)
def calcular_asistencia(entradas, dias_por_semana):
    if dias_por_semana == 7:
        dias_por_semana = OBJETIVO_PLAN_LIBRE
    return min(round(100 * entradas / (dias_por_semana * 4)), 100)


# REGLA 14: nivel que se sugiere, o None si todavía no corresponde subir
def calcular_nivel_sugerido(nivel, entradas, cumplimiento):
    if entradas < ENTRADAS_PARA_SUBIR or cumplimiento < CUMPLIMIENTO_PARA_SUBIR:
        return None
    if nivel not in NIVELES or nivel == NIVELES[-1]:
        return None
    return NIVELES[NIVELES.index(nivel) + 1]


# REGLA 5: rutina según objetivo y nivel
def buscar_rutina(objetivo, nivel):
    return consultar_uno(
        "SELECT id, nombre, descripcion FROM rutinas WHERE objetivo = %s AND nivel = %s",
        (objetivo, nivel),
    )


def buscar_ultimo_dia(socio_id, rutina_id):
    # Último día de esa rutina que hizo el socio (o None)
    fila = consultar_uno(
        "SELECT dia_rutina FROM asistencias WHERE socio_id = %s AND rutina_id = %s "
        "ORDER BY fecha_hora DESC, id DESC LIMIT 1",
        (socio_id, rutina_id),
    )
    if fila is None:
        return None
    return fila["dia_rutina"]


# Ejercicios de un día de rutina. Si se pasa una entrada, indica cuáles se hicieron en ella.
def buscar_ejercicios(rutina_id, dia, asistencia_id=None):
    ejercicios = consultar(
        "SELECT e.id, e.nombre, e.series_repeticiones, er.id IS NOT NULL AS hecho "
        "FROM rutina_ejercicios e "
        "LEFT JOIN ejercicios_realizados er ON er.ejercicio_id = e.id AND er.asistencia_id = %s "
        "WHERE e.rutina_id = %s AND e.dia = %s ORDER BY e.orden",
        (asistencia_id, rutina_id, dia),
    )
    for ejercicio in ejercicios:
        ejercicio["hecho"] = bool(ejercicio["hecho"])
    return ejercicios


# Junta todo lo que muestra la ficha sobre la rutina (REGLAS 11 a 14)
def armar_seguimiento(socio_id, nivel, dias_por_semana, rutina):
    # Entradas de la ventana, de la más reciente a la más antigua
    filas = consultar(
        "SELECT a.id, a.fecha, a.fecha = CURDATE() AS es_hoy, a.rutina_id, a.dia_rutina, r.nombre AS rutina "
        "FROM asistencias a LEFT JOIN rutinas r ON a.rutina_id = r.id "
        "WHERE a.socio_id = %s AND a.fecha_hora >= NOW() - INTERVAL %s DAY "
        "ORDER BY a.fecha_hora DESC, a.id DESC",
        (socio_id, VENTANA_DIAS),
    )

    entradas = []
    entradas_rutina_actual = 0
    realizados = 0
    asignados = 0
    dia_de_hoy = None

    for fila in filas:
        # Las entradas anteriores a esta función no tienen rutina
        if fila["rutina_id"] is None:
            continue

        ejercicios = buscar_ejercicios(fila["rutina_id"], fila["dia_rutina"], fila["id"])
        hechos = sum(1 for ejercicio in ejercicios if ejercicio["hecho"])
        entradas.append({
            "id": fila["id"],
            "fecha": str(fila["fecha"]),
            "rutina": fila["rutina"],
            "dia": fila["dia_rutina"],
            "ejercicios": ejercicios,
        })

        # El cumplimiento solo cuenta la rutina actual
        if rutina is not None and fila["rutina_id"] == rutina["id"]:
            entradas_rutina_actual += 1
            realizados += hechos
            asignados += len(ejercicios)
            if fila["es_hoy"]:
                dia_de_hoy = fila["dia_rutina"]

    cumplimiento = calcular_cumplimiento(realizados, asignados)

    # El día que le toca: el de hoy si ya entró; si no, el siguiente
    dia_actual = None
    ejercicios_del_dia = []
    if rutina is not None:
        dia_actual = dia_de_hoy
        if dia_actual is None:
            dia_actual = calcular_siguiente_dia(buscar_ultimo_dia(socio_id, rutina["id"]))
        ejercicios_del_dia = buscar_ejercicios(rutina["id"], dia_actual)

    return {
        "dia_actual": dia_actual,
        "ejercicios_del_dia": ejercicios_del_dia,
        "entradas": entradas,
        "cumplimiento": cumplimiento,
        "asistencia": calcular_asistencia(len(filas), dias_por_semana),
        "nivel_sugerido": calcular_nivel_sugerido(nivel, entradas_rutina_actual, cumplimiento),
    }


# Cuenta las entradas del socio en los últimos 7 días (usado en la regla 3)
def contar_entradas_semana(socio_id):
    fila = consultar_uno(
        "SELECT COUNT(*) AS total FROM asistencias "
        "WHERE socio_id = %s AND fecha_hora >= NOW() - INTERVAL 7 DAY",
        (socio_id,),
    )
    return fila["total"]


# Guarda un pago (REGLA 7), dentro de la transacción que cambia el vencimiento.
# El monto se copia del plan: cambiar el precio no altera los pagos anteriores.
def guardar_pago(cursor, socio_id, plan, dias_restantes, vencimiento_nuevo):
    cursor.execute(
        "INSERT INTO pagos (socio_id, plan_id, fecha, monto, dias_plan, dias_restantes, vencimiento_nuevo) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (socio_id, plan["id"], date.today(), plan["precio"], plan["duracion_dias"],
         dias_restantes, vencimiento_nuevo),
    )


# ---------------------------------------------
# LOGIN Y PERMISOS (REGLA 15)
# ---------------------------------------------

# Toda ruta /api/ necesita sesión, salvo el login.
# El usuario se busca en cada pedido: si lo desactivan, pierde el acceso enseguida.
@app.before_request
def exigir_sesion():
    if not request.path.startswith("/api/") or request.path == "/api/login":
        return None

    usuario = None
    if "usuario_id" in session:
        usuario = consultar_uno(
            "SELECT id, nombre, usuario, rol FROM usuarios WHERE id = %s AND activo = 1",
            (session["usuario_id"],),
        )
    if usuario is None:
        session.clear()
        return error("Hay que iniciar sesión", 401)

    g.usuario = usuario
    return None


# Se pone sobre las rutas que solo puede usar el administrador
def solo_admin(ruta):
    @wraps(ruta)
    def ruta_protegida(*args, **kwargs):
        if g.usuario["rol"] != "admin":
            return error("No tienes permiso para hacer esto", 403)
        return ruta(*args, **kwargs)
    return ruta_protegida


# ---------------------------------------------
# PÁGINA PRINCIPAL
# ---------------------------------------------

@app.route("/")
def inicio():
    return app.send_static_file("index.html")


# ---------------------------------------------
# API
# ---------------------------------------------

# 1. Lista de planes (para los desplegables)
@app.route("/api/planes")
def listar_planes():
    planes = consultar("SELECT * FROM planes ORDER BY id")
    for plan in planes:
        plan["precio"] = float(plan["precio"])
    return jsonify(planes)


# Cambiar el precio de un plan
@app.route("/api/planes/<int:plan_id>", methods=["PUT"])
@solo_admin
def cambiar_precio(plan_id):
    datos = leer_json()

    if consultar_uno("SELECT id FROM planes WHERE id = %s", (plan_id,)) is None:
        return error("El plan no existe", 404)

    precio = leer_numero(datos.get("precio"))
    if precio is None or precio < PRECIO_MINIMO or precio > PRECIO_MAXIMO:
        return error("El precio debe ser mayor que 0")

    ejecutar("UPDATE planes SET precio = %s WHERE id = %s", (precio, plan_id))
    return jsonify({"mensaje": "Precio actualizado"})


# 2. Lista de socios con su estado
@app.route("/api/socios")
def listar_socios():
    texto = request.args.get("q", "").strip()
    filtro_estado = request.args.get("estado")
    estados = ("Activo", "Por vencer", "Vencido", "Congelado", "Cancelado")
    if filtro_estado is not None and filtro_estado not in estados:
        return error("El estado no es válido")

    condicion = ""
    parametros = ()
    if texto:
        # ! es el escape de LIKE: %, _ y el propio ! se buscan como texto.
        texto = texto.replace("!", "!!").replace("%", "!%").replace("_", "!_")
        patron = "%" + texto + "%"
        condicion = "WHERE (s.nombre LIKE %s ESCAPE '!' OR s.ci LIKE %s ESCAPE '!') "
        parametros = (patron, patron)

    socios = consultar(
        "SELECT s.id, s.nombre, s.ci, p.nombre AS plan, s.fecha_vencimiento, s.fecha_cancelacion, "
        + SQL_CONGELADO +
        " FROM socios s JOIN planes p ON s.plan_id = p.id "
        + condicion + "ORDER BY s.nombre",
        parametros,
    )

    # REGLA 8: los cancelados solo se muestran si se piden con ?estado=Cancelado
    resultado = []
    for socio in socios:
        estado = estado_del_socio(socio)
        if filtro_estado is not None:
            if estado != filtro_estado:
                continue
        elif estado == "Cancelado":
            continue
        resultado.append({
            "id": socio["id"],
            "nombre": socio["nombre"],
            "ci": socio["ci"],
            "plan": socio["plan"],
            "fecha_vencimiento": str(socio["fecha_vencimiento"]),
            "estado": estado,
        })
    return jsonify(resultado)


# 3. Alta de socio
@app.route("/api/socios", methods=["POST"])
def crear_socio():
    datos = leer_json()

    mensaje = validar_datos_socio(datos, ["nombre", "ci", "peso", "altura", "objetivo", "nivel", "plan_id"])
    if mensaje:
        return error(mensaje)

    peso = float(datos["peso"])
    altura = float(datos["altura"])

    if consultar_uno("SELECT id FROM socios WHERE ci = %s", (datos["ci"],)):
        return error("Ya existe un socio con ese CI")

    plan = consultar_uno("SELECT * FROM planes WHERE id = %s", (leer_entero(datos["plan_id"]),))
    if plan is None:
        return error("El plan no existe")

    # REGLA 1: socio nuevo, el plan empieza hoy
    fecha_vencimiento = calcular_vencimiento(None, plan["duracion_dias"])

    # El socio, su primer peso y su primer pago se guardan juntos
    try:
        with transaccion() as cursor:
            cursor.execute(
                "INSERT INTO socios (nombre, ci, telefono, peso, altura, objetivo, nivel, plan_id, fecha_vencimiento) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (datos["nombre"], datos["ci"], datos.get("telefono", ""), peso, altura,
                 datos["objetivo"], datos["nivel"], plan["id"], fecha_vencimiento),
            )
            socio_id = cursor.lastrowid

            # Primer registro del historial de peso
            cursor.execute(
                "INSERT INTO registros_peso (socio_id, fecha, peso) VALUES (%s, %s, %s)",
                (socio_id, date.today(), peso),
            )

            # REGLA 7: un socio nuevo no tiene días restantes
            guardar_pago(cursor, socio_id, plan, 0, fecha_vencimiento)
    except mysql.connector.IntegrityError:
        # Otro pedido guardó el mismo CI justo después de la comprobación de arriba
        return error("Ya existe un socio con ese CI")

    return jsonify({"mensaje": "Socio dado de alta", "id": socio_id})


# 4. Eliminar un socio
@app.route("/api/socios/<int:socio_id>", methods=["DELETE"])
@solo_admin
def eliminar_socio(socio_id):
    if not socio_existe(socio_id):
        return error("El socio no existe", 404)

    # Primero las tablas que dependen del socio (por las claves foráneas)
    with transaccion() as cursor:
        cursor.execute(
            "DELETE er FROM ejercicios_realizados er "
            "JOIN asistencias a ON er.asistencia_id = a.id WHERE a.socio_id = %s",
            (socio_id,),
        )
        cursor.execute("DELETE FROM asistencias WHERE socio_id = %s", (socio_id,))
        cursor.execute("DELETE FROM registros_peso WHERE socio_id = %s", (socio_id,))
        cursor.execute("DELETE FROM pagos WHERE socio_id = %s", (socio_id,))
        cursor.execute("DELETE FROM congelamientos WHERE socio_id = %s", (socio_id,))
        cursor.execute("DELETE FROM auditoria_socios WHERE socio_id = %s", (socio_id,))
        cursor.execute("DELETE FROM socios WHERE id = %s", (socio_id,))
    return jsonify({"mensaje": "Socio eliminado correctamente"})


# 5. Editar los datos de un socio (el peso y el plan se cambian por sus propias rutas)
@app.route("/api/socios/<int:socio_id>", methods=["PUT"])
def editar_socio(socio_id):
    datos = leer_json()

    if not socio_existe(socio_id):
        return error("El socio no existe", 404)

    mensaje = validar_datos_socio(datos, ["nombre", "ci", "altura", "objetivo", "nivel"])
    if mensaje:
        return error(mensaje)
    altura = float(datos["altura"])

    # El CI no puede ser el de otro socio (el suyo propio sí)
    if consultar_uno("SELECT id FROM socios WHERE ci = %s AND id <> %s", (datos["ci"], socio_id)):
        return error("Ya existe otro socio con ese CI")

    try:
        ejecutar(
            "UPDATE socios SET nombre = %s, ci = %s, telefono = %s, altura = %s, objetivo = %s, nivel = %s "
            "WHERE id = %s",
            (datos["nombre"], datos["ci"], datos.get("telefono", ""), altura,
             datos["objetivo"], datos["nivel"], socio_id),
        )
    except mysql.connector.IntegrityError:
        # Otro pedido guardó el mismo CI justo después de la comprobación de arriba
        return error("Ya existe otro socio con ese CI")
    return jsonify({"mensaje": "Datos actualizados"})


# 6. Ficha completa de un socio
@app.route("/api/socios/<int:socio_id>")
def ver_socio(socio_id):
    socio = consultar_uno(
        "SELECT s.*, p.nombre AS plan, p.dias_por_semana, " + SQL_CONGELADO +
        " FROM socios s JOIN planes p ON s.plan_id = p.id "
        "WHERE s.id = %s",
        (socio_id,),
    )
    if socio is None:
        return error("El socio no existe", 404)

    peso = float(socio["peso"])
    altura = float(socio["altura"])

    # REGLA 4: IMC
    imc, categoria = calcular_imc(peso, altura)

    # REGLA 5: rutina según objetivo y nivel
    rutina = buscar_rutina(socio["objetivo"], socio["nivel"])

    # Historial de peso, del más antiguo al más reciente
    historial = consultar(
        "SELECT fecha, peso FROM registros_peso WHERE socio_id = %s ORDER BY fecha, id",
        (socio_id,),
    )
    for registro in historial:
        registro["fecha"] = str(registro["fecha"])
        registro["peso"] = float(registro["peso"])

    # REGLA 6: progreso (hacen falta al menos 2 pesos para comparar)
    if len(historial) < 2:
        progreso = {"diferencia": 0, "resultado": "Faltan datos"}
    else:
        diferencia, resultado = calcular_progreso(
            socio["objetivo"], historial[0]["peso"], historial[-1]["peso"]
        )
        progreso = {"diferencia": diferencia, "resultado": resultado}

    # REGLA 7: historial de pagos, del más reciente al más antiguo
    pagos = consultar(
        "SELECT pa.fecha, pl.nombre AS plan, pa.monto, pa.dias_plan, pa.dias_restantes, pa.vencimiento_nuevo "
        "FROM pagos pa JOIN planes pl ON pa.plan_id = pl.id "
        "WHERE pa.socio_id = %s ORDER BY pa.fecha DESC, pa.id DESC",
        (socio_id,),
    )
    for pago in pagos:
        pago["fecha"] = str(pago["fecha"])
        pago["monto"] = float(pago["monto"])
        pago["vencimiento_nuevo"] = str(pago["vencimiento_nuevo"])

    # T4: cambios de plan o vencimiento, incluidos congelar y descongelar.
    auditoria = consultar(
        "SELECT a.plan_anterior, pa.nombre AS nombre_plan_anterior, "
        "a.plan_nuevo, pn.nombre AS nombre_plan_nuevo, "
        "a.vencimiento_anterior, a.vencimiento_nuevo, a.fecha_hora "
        "FROM auditoria_socios a "
        "JOIN planes pa ON pa.id = a.plan_anterior "
        "JOIN planes pn ON pn.id = a.plan_nuevo "
        "WHERE a.socio_id = %s ORDER BY a.fecha_hora DESC, a.id DESC",
        (socio_id,),
    )
    for cambio in auditoria:
        for campo in ("vencimiento_anterior", "vencimiento_nuevo", "fecha_hora"):
            cambio[campo] = str(cambio[campo])

    return jsonify({
        "id": socio["id"],
        "nombre": socio["nombre"],
        "ci": socio["ci"],
        "telefono": socio["telefono"],
        "peso": peso,
        "altura": altura,
        "objetivo": socio["objetivo"],
        "nivel": socio["nivel"],
        "plan_id": socio["plan_id"],
        "plan": socio["plan"],
        "dias_por_semana": socio["dias_por_semana"],
        "fecha_vencimiento": str(socio["fecha_vencimiento"]),
        "estado": estado_del_socio(socio),
        "entradas_semana": contar_entradas_semana(socio_id),
        "imc": imc,
        "categoria_imc": categoria,
        "rutina": rutina,
        "seguimiento": armar_seguimiento(socio_id, socio["nivel"], socio["dias_por_semana"], rutina),
        "progreso": progreso,
        "historial_peso": historial,
        "pagos": pagos,
        "auditoria": auditoria,
    })


# 7. Check-in (REGLA 3)
@app.route("/api/socios/<int:socio_id>/checkin", methods=["POST"])
def hacer_checkin(socio_id):
    socio = consultar_uno(
        "SELECT s.fecha_vencimiento, s.fecha_cancelacion, s.objetivo, s.nivel, p.dias_por_semana, " + SQL_CONGELADO +
        " FROM socios s JOIN planes p ON s.plan_id = p.id "
        "WHERE s.id = %s",
        (socio_id,),
    )
    if socio is None:
        return error("El socio no existe", 404)

    # a) El plan tiene que estar en uso: ni cancelado, ni congelado, ni vencido
    estado = estado_del_socio(socio)
    if estado == "Cancelado":
        return error("Socio cancelado")
    if estado == "Congelado":
        return error("Plan congelado")
    if estado == "Vencido":
        return error("Plan vencido")

    # b) Solo una entrada por día
    hoy = consultar_uno(
        "SELECT COUNT(*) AS total FROM asistencias "
        "WHERE socio_id = %s AND DATE(fecha_hora) = CURDATE()",
        (socio_id,),
    )
    if hoy["total"] > 0:
        return error("Ya entró hoy")

    # c) No superar los días por semana de su plan (últimos 7 días)
    if contar_entradas_semana(socio_id) >= socio["dias_por_semana"]:
        return error("Ya usó sus " + str(socio["dias_por_semana"]) + " días de los últimos 7")

    # REGLA 11: la entrada guarda la rutina actual y el día que le toca
    rutina = buscar_rutina(socio["objetivo"], socio["nivel"])
    rutina_id = None
    dia = None
    if rutina is not None:
        rutina_id = rutina["id"]
        dia = calcular_siguiente_dia(buscar_ultimo_dia(socio_id, rutina_id))

    # Si dos pedidos llegan a la vez, el UNIQUE de la tabla rechaza el segundo
    try:
        ejecutar(
            "INSERT INTO asistencias (socio_id, fecha_hora, rutina_id, dia_rutina) VALUES (%s, NOW(), %s, %s)",
            (socio_id, rutina_id, dia),
        )
    except mysql.connector.IntegrityError:
        return error("Ya entró hoy")

    if dia is None:
        return jsonify({"mensaje": "Entrada registrada"})
    return jsonify({"mensaje": "Entrada registrada: hoy le toca el Día " + str(dia)})


# 8. Renovar plan (se puede cambiar de plan)
@app.route("/api/socios/<int:socio_id>/renovar", methods=["POST"])
def renovar(socio_id):
    datos = leer_json()

    socio = buscar_socio(socio_id)
    if socio is None:
        return error("El socio no existe", 404)

    estado = estado_del_socio(socio)
    if estado == "Congelado":
        return error("No se puede renovar un plan congelado")

    plan_id = leer_entero(datos.get("plan_id"))
    if plan_id is None:
        return error("El plan no es válido")

    plan = consultar_uno("SELECT * FROM planes WHERE id = %s", (plan_id,))
    if plan is None:
        return error("El plan no existe")

    # REGLA 8: un cancelado vuelve desde hoy, sin los días que le quedaban
    vencimiento_actual = socio["fecha_vencimiento"]
    if estado == "Cancelado":
        vencimiento_actual = None

    # REGLA 1: si sigue activo, se suman los días a lo que le queda
    nueva_fecha = calcular_vencimiento(vencimiento_actual, plan["duracion_dias"])

    # REGLA 7: el pago deja registrados los días que le quedaban
    dias_restantes = calcular_dias_restantes(vencimiento_actual)

    with transaccion() as cursor:
        cursor.execute(
            "UPDATE socios SET plan_id = %s, fecha_vencimiento = %s, fecha_cancelacion = NULL WHERE id = %s",
            (plan["id"], nueva_fecha, socio_id),
        )
        guardar_pago(cursor, socio_id, plan, dias_restantes, nueva_fecha)

    return jsonify({
        "mensaje": "Plan renovado hasta " + str(nueva_fecha) + " ("
        + str(plan["duracion_dias"]) + " días del plan + "
        + str(dias_restantes) + " que le quedaban)"
    })


# 10. Cancelar un socio (REGLA 8): se conserva todo su historial
@app.route("/api/socios/<int:socio_id>/cancelar", methods=["POST"])
def cancelar_socio(socio_id):
    socio = buscar_socio(socio_id)
    if socio is None:
        return error("El socio no existe", 404)

    estado = estado_del_socio(socio)
    if estado == "Cancelado":
        return error("El socio ya está cancelado")
    if estado == "Congelado":
        return error("Hay que descongelar el plan antes de cancelar")

    ejecutar("UPDATE socios SET fecha_cancelacion = CURDATE() WHERE id = %s", (socio_id,))
    return jsonify({"mensaje": "Socio cancelado"})


# 11. Congelar un plan (REGLA 9)
# Los días se suman al vencimiento de inmediato: el congelamiento termina solo al llegar a fecha_fin.
@app.route("/api/socios/<int:socio_id>/congelar", methods=["POST"])
def congelar_plan(socio_id):
    datos = leer_json()

    socio = buscar_socio(socio_id)
    if socio is None:
        return error("El socio no existe", 404)

    if estado_del_socio(socio) not in ("Activo", "Por vencer"):
        return error("Solo se puede congelar un plan en uso")

    dias = leer_entero(datos.get("dias"))
    if dias is None or dias < 1 or dias > CONGELAMIENTO_MAXIMO:
        return error("Los días deben estar entre 1 y " + str(CONGELAMIENTO_MAXIMO))

    # Un congelamiento por período: el período empieza en el último pago
    repetido = consultar_uno(
        "SELECT c.id FROM congelamientos c WHERE c.socio_id = %s AND c.fecha_inicio >= "
        "COALESCE((SELECT MAX(fecha) FROM pagos WHERE socio_id = %s), '1000-01-01')",
        (socio_id, socio_id),
    )
    if repetido:
        return error("Ya usó su congelamiento de este período")

    hoy = date.today()
    fecha_fin = hoy + timedelta(days=dias)
    with transaccion() as cursor:
        cursor.execute(
            "INSERT INTO congelamientos (socio_id, fecha_inicio, fecha_fin) VALUES (%s, %s, %s)",
            (socio_id, hoy, fecha_fin),
        )
        cursor.execute(
            "UPDATE socios SET fecha_vencimiento = %s WHERE id = %s",
            (socio["fecha_vencimiento"] + timedelta(days=dias), socio_id),
        )
    return jsonify({"mensaje": "Plan congelado hasta " + str(fecha_fin)})


# 12. Terminar un congelamiento antes de tiempo (REGLA 9): se restan los días no usados
@app.route("/api/socios/<int:socio_id>/descongelar", methods=["POST"])
def descongelar_plan(socio_id):
    socio = buscar_socio(socio_id)
    if socio is None:
        return error("El socio no existe", 404)

    congelamiento = consultar_uno(
        "SELECT id, fecha_fin FROM congelamientos "
        "WHERE socio_id = %s AND fecha_inicio <= CURDATE() AND CURDATE() < fecha_fin",
        (socio_id,),
    )
    if congelamiento is None:
        return error("El plan no está congelado")

    dias_no_usados = calcular_dias_no_usados(congelamiento["fecha_fin"])
    with transaccion() as cursor:
        cursor.execute(
            "UPDATE congelamientos SET fecha_fin = %s WHERE id = %s",
            (date.today(), congelamiento["id"]),
        )
        cursor.execute(
            "UPDATE socios SET fecha_vencimiento = %s WHERE id = %s",
            (socio["fecha_vencimiento"] - timedelta(days=dias_no_usados), socio_id),
        )
    return jsonify({"mensaje": "Plan descongelado. Se restaron " + str(dias_no_usados) + " días no usados"})


# 13. Marcar o desmarcar un ejercicio de una entrada (REGLA 12)
@app.route("/api/socios/<int:socio_id>/asistencias/<int:asistencia_id>/ejercicios/<int:ejercicio_id>",
           methods=["POST", "DELETE"])
def marcar_ejercicio(socio_id, asistencia_id, ejercicio_id):
    # La entrada debe ser del socio, y el ejercicio de la rutina y el día de esa entrada
    valido = consultar_uno(
        "SELECT a.id FROM asistencias a "
        "JOIN rutina_ejercicios e ON e.rutina_id = a.rutina_id AND e.dia = a.dia_rutina "
        "WHERE a.id = %s AND a.socio_id = %s AND e.id = %s",
        (asistencia_id, socio_id, ejercicio_id),
    )
    if valido is None:
        return error("Ese ejercicio no corresponde a esa entrada", 404)

    if request.method == "POST":
        # INSERT IGNORE: marcar dos veces no es un error
        ejecutar(
            "INSERT IGNORE INTO ejercicios_realizados (asistencia_id, ejercicio_id) VALUES (%s, %s)",
            (asistencia_id, ejercicio_id),
        )
        return jsonify({"mensaje": "Ejercicio marcado"})

    ejecutar(
        "DELETE FROM ejercicios_realizados WHERE asistencia_id = %s AND ejercicio_id = %s",
        (asistencia_id, ejercicio_id),
    )
    return jsonify({"mensaje": "Ejercicio desmarcado"})


# 14. Subir de nivel (REGLA 14): lo confirma una persona, y se vuelve a comprobar la regla
@app.route("/api/socios/<int:socio_id>/subir-nivel", methods=["POST"])
def subir_nivel(socio_id):
    socio = consultar_uno(
        "SELECT s.objetivo, s.nivel, p.dias_por_semana "
        "FROM socios s JOIN planes p ON s.plan_id = p.id WHERE s.id = %s",
        (socio_id,),
    )
    if socio is None:
        return error("El socio no existe", 404)

    rutina = buscar_rutina(socio["objetivo"], socio["nivel"])
    seguimiento = armar_seguimiento(socio_id, socio["nivel"], socio["dias_por_semana"], rutina)
    nivel_nuevo = seguimiento["nivel_sugerido"]
    if nivel_nuevo is None:
        return error("Todavía no cumple las condiciones para subir de nivel")

    ejecutar("UPDATE socios SET nivel = %s WHERE id = %s", (nivel_nuevo, socio_id))
    return jsonify({"mensaje": "Nivel actualizado a " + nivel_nuevo})


# 15. Iniciar sesión (REGLA 15): el mismo mensaje para cualquier fallo
@app.route("/api/login", methods=["POST"])
def iniciar_sesion():
    datos = leer_json()
    nombre_usuario = datos.get("usuario")
    clave = datos.get("clave")

    usuario = None
    if isinstance(nombre_usuario, str) and isinstance(clave, str):
        usuario = consultar_uno(
            "SELECT id, clave_hash FROM usuarios WHERE usuario = %s AND activo = 1",
            (nombre_usuario,),
        )
    if usuario is None or not check_password_hash(usuario["clave_hash"], clave):
        return error("Usuario o contraseña incorrectos", 401)

    session.clear()
    session["usuario_id"] = usuario["id"]
    return jsonify({"mensaje": "Sesión iniciada"})


# 16. Cerrar sesión
@app.route("/api/logout", methods=["POST"])
def cerrar_sesion():
    session.clear()
    return jsonify({"mensaje": "Sesión cerrada"})


# 17. Quién tiene la sesión abierta
@app.route("/api/sesion")
def ver_sesion():
    return jsonify(g.usuario)


# 18. Listado de usuarios
@app.route("/api/usuarios")
@solo_admin
def listar_usuarios():
    usuarios = consultar("SELECT id, nombre, usuario, rol, activo FROM usuarios ORDER BY nombre")
    for usuario in usuarios:
        usuario["activo"] = bool(usuario["activo"])
    return jsonify(usuarios)


# 19. Crear un usuario
@app.route("/api/usuarios", methods=["POST"])
@solo_admin
def crear_usuario():
    datos = leer_json()

    for campo, largo in LARGO_MAXIMO_USUARIO.items():
        valor = datos.get(campo)
        if not isinstance(valor, str) or valor.strip() == "":
            return error("Falta el campo: " + campo)
        if len(valor) > largo:
            return error("El campo " + campo + " admite hasta " + str(largo) + " caracteres")

    clave = datos.get("clave")
    if not isinstance(clave, str) or len(clave) < CLAVE_MINIMA:
        return error("La contraseña debe tener al menos " + str(CLAVE_MINIMA) + " caracteres")

    if datos.get("rol") not in ROLES:
        return error("El rol no es válido")

    try:
        ejecutar(
            "INSERT INTO usuarios (nombre, usuario, clave_hash, rol) VALUES (%s, %s, %s, %s)",
            (datos["nombre"], datos["usuario"], generate_password_hash(clave), datos["rol"]),
        )
    except mysql.connector.IntegrityError:
        return error("Ya existe un usuario con ese nombre de usuario")
    return jsonify({"mensaje": "Usuario creado"})


# 20. Activar o desactivar un usuario
@app.route("/api/usuarios/<int:usuario_id>", methods=["PATCH"])
@solo_admin
def cambiar_activo(usuario_id):
    datos = leer_json()

    activo = datos.get("activo")
    if not isinstance(activo, bool):
        return error("El campo activo debe ser verdadero o falso")

    if consultar_uno("SELECT id FROM usuarios WHERE id = %s", (usuario_id,)) is None:
        return error("El usuario no existe", 404)

    if usuario_id == g.usuario["id"] and not activo:
        return error("No puedes desactivar tu propio usuario")

    ejecutar("UPDATE usuarios SET activo = %s WHERE id = %s", (activo, usuario_id))
    if activo:
        return jsonify({"mensaje": "Usuario activado"})
    return jsonify({"mensaje": "Usuario desactivado"})


# 9. Registrar un nuevo peso
@app.route("/api/socios/<int:socio_id>/peso", methods=["POST"])
def registrar_peso(socio_id):
    datos = leer_json()

    if not socio_existe(socio_id):
        return error("El socio no existe", 404)

    mensaje = validar_peso(datos.get("peso"))
    if mensaje:
        return error(mensaje)
    peso = float(datos["peso"])

    # El trigger copia el peso a socios dentro de esta misma transacción.
    with transaccion() as cursor:
        cursor.execute(
            "INSERT INTO registros_peso (socio_id, fecha, peso) VALUES (%s, %s, %s)",
            (socio_id, date.today(), peso),
        )
    return jsonify({"mensaje": "Peso registrado"})


if __name__ == "__main__":
    # El modo debug solo se activa con la variable de entorno GIMNASIO_DEBUG=1
    app.run(debug=os.environ.get("GIMNASIO_DEBUG") == "1", port=5001)
