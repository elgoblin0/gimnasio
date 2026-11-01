# =============================================
# Backend del sistema de gimnasio (Flask + MySQL)
# Ejecutar con: python3 app.py
# Abrir en el navegador: http://localhost:5001
# =============================================

import math
import os
from contextlib import contextmanager
from datetime import date, timedelta

import mysql.connector
from flask import Flask, jsonify, request

# static_url_path="" hace que los archivos de static/ se sirvan desde la raíz
# (ej: http://localhost:5001/socio.html)
app = Flask(__name__, static_folder="static", static_url_path="")

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


# REGLA 2: estado del socio según los días que le quedan
def calcular_estado(fecha_vencimiento):
    dias_restantes = (fecha_vencimiento - date.today()).days
    if dias_restantes < 0:
        return "Vencido"
    if dias_restantes <= 7:
        return "Por vencer"
    return "Activo"


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
    socios = consultar(
        "SELECT s.id, s.nombre, s.ci, p.nombre AS plan, s.fecha_vencimiento "
        "FROM socios s JOIN planes p ON s.plan_id = p.id "
        "ORDER BY s.nombre"
    )
    for socio in socios:
        socio["estado"] = calcular_estado(socio["fecha_vencimiento"])
        socio["fecha_vencimiento"] = str(socio["fecha_vencimiento"])
    return jsonify(socios)


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
def eliminar_socio(socio_id):
    if not socio_existe(socio_id):
        return error("El socio no existe", 404)

    # Primero las tablas que dependen del socio (por las claves foráneas)
    with transaccion() as cursor:
        cursor.execute("DELETE FROM asistencias WHERE socio_id = %s", (socio_id,))
        cursor.execute("DELETE FROM registros_peso WHERE socio_id = %s", (socio_id,))
        cursor.execute("DELETE FROM pagos WHERE socio_id = %s", (socio_id,))
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
        "SELECT s.*, p.nombre AS plan, p.dias_por_semana "
        "FROM socios s JOIN planes p ON s.plan_id = p.id "
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
    rutina = consultar_uno(
        "SELECT nombre, descripcion FROM rutinas WHERE objetivo = %s AND nivel = %s",
        (socio["objetivo"], socio["nivel"]),
    )

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
        "estado": calcular_estado(socio["fecha_vencimiento"]),
        "entradas_semana": contar_entradas_semana(socio_id),
        "imc": imc,
        "categoria_imc": categoria,
        "rutina": rutina,
        "progreso": progreso,
        "historial_peso": historial,
        "pagos": pagos,
    })


# 7. Check-in (REGLA 3)
@app.route("/api/socios/<int:socio_id>/checkin", methods=["POST"])
def hacer_checkin(socio_id):
    socio = consultar_uno(
        "SELECT s.fecha_vencimiento, p.dias_por_semana "
        "FROM socios s JOIN planes p ON s.plan_id = p.id "
        "WHERE s.id = %s",
        (socio_id,),
    )
    if socio is None:
        return error("El socio no existe", 404)

    # a) El plan no puede estar vencido
    if calcular_estado(socio["fecha_vencimiento"]) == "Vencido":
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

    # Si dos pedidos llegan a la vez, el UNIQUE de la tabla rechaza el segundo
    try:
        ejecutar("INSERT INTO asistencias (socio_id, fecha_hora) VALUES (%s, NOW())", (socio_id,))
    except mysql.connector.IntegrityError:
        return error("Ya entró hoy")
    return jsonify({"mensaje": "Entrada registrada"})


# 8. Renovar plan (se puede cambiar de plan)
@app.route("/api/socios/<int:socio_id>/renovar", methods=["POST"])
def renovar(socio_id):
    datos = leer_json()

    socio = consultar_uno("SELECT fecha_vencimiento FROM socios WHERE id = %s", (socio_id,))
    if socio is None:
        return error("El socio no existe", 404)

    plan_id = leer_entero(datos.get("plan_id"))
    if plan_id is None:
        return error("El plan no es válido")

    plan = consultar_uno("SELECT * FROM planes WHERE id = %s", (plan_id,))
    if plan is None:
        return error("El plan no existe")

    # REGLA 1: si sigue activo, se suman los días a lo que le queda
    nueva_fecha = calcular_vencimiento(socio["fecha_vencimiento"], plan["duracion_dias"])

    # REGLA 7: el pago deja registrados los días que le quedaban
    dias_restantes = calcular_dias_restantes(socio["fecha_vencimiento"])

    with transaccion() as cursor:
        cursor.execute(
            "UPDATE socios SET plan_id = %s, fecha_vencimiento = %s WHERE id = %s",
            (plan["id"], nueva_fecha, socio_id),
        )
        guardar_pago(cursor, socio_id, plan, dias_restantes, nueva_fecha)

    return jsonify({
        "mensaje": "Plan renovado hasta " + str(nueva_fecha) + " ("
        + str(plan["duracion_dias"]) + " días del plan + "
        + str(dias_restantes) + " que le quedaban)"
    })


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

    # El historial y el peso actual se guardan juntos
    with transaccion() as cursor:
        cursor.execute(
            "INSERT INTO registros_peso (socio_id, fecha, peso) VALUES (%s, %s, %s)",
            (socio_id, date.today(), peso),
        )
        cursor.execute("UPDATE socios SET peso = %s WHERE id = %s", (peso, socio_id))
    return jsonify({"mensaje": "Peso registrado"})


if __name__ == "__main__":
    # El modo debug solo se activa con la variable de entorno GIMNASIO_DEBUG=1
    app.run(debug=os.environ.get("GIMNASIO_DEBUG") == "1", port=5001)
