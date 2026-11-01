# =============================================
# Pruebas de las reglas del gimnasio
# No hacen falta MySQL ni librerías nuevas.
# Ejecutar desde la carpeta del proyecto con:
#   python3 -m unittest tests.test_reglas
# =============================================

import unittest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import app as gimnasio


def dias_desde_hoy(dias):
    return date.today() + timedelta(days=dias)


def socio_valido(**cambios):
    datos = {
        "nombre": "Ana Lopez",
        "ci": "11111111A",
        "telefono": "600111111",
        "peso": "68",
        "altura": "1.65",
        "objetivo": "bajar peso",
        "nivel": "principiante",
        "plan_id": "1",
    }
    datos.update(cambios)
    return datos


CAMPOS_ALTA = ["nombre", "ci", "peso", "altura", "objetivo", "nivel", "plan_id"]


class TestVencimiento(unittest.TestCase):  # REGLA 1
    def test_socio_nuevo_cuenta_desde_hoy(self):
        self.assertEqual(gimnasio.calcular_vencimiento(None, 30), dias_desde_hoy(30))

    def test_socio_activo_suma_a_lo_que_le_queda(self):
        self.assertEqual(gimnasio.calcular_vencimiento(dias_desde_hoy(5), 30), dias_desde_hoy(35))

    def test_ultimo_dia_todavia_suma(self):
        self.assertEqual(gimnasio.calcular_vencimiento(date.today(), 30), dias_desde_hoy(30))

    def test_vencido_ayer_cuenta_desde_hoy(self):
        self.assertEqual(gimnasio.calcular_vencimiento(dias_desde_hoy(-1), 30), dias_desde_hoy(30))


class TestDiasRestantes(unittest.TestCase):  # REGLA 7
    def test_casos(self):
        casos = [(None, 0), (dias_desde_hoy(-1), 0), (date.today(), 0), (dias_desde_hoy(5), 5)]
        for fecha, esperado in casos:
            with self.subTest(fecha=fecha):
                self.assertEqual(gimnasio.calcular_dias_restantes(fecha), esperado)

    def test_el_vencimiento_es_hoy_mas_plan_mas_restantes(self):
        fecha = dias_desde_hoy(5)
        nuevo = gimnasio.calcular_vencimiento(fecha, 30)
        self.assertEqual(nuevo, dias_desde_hoy(30 + gimnasio.calcular_dias_restantes(fecha)))


class TestEstado(unittest.TestCase):  # REGLA 2
    def test_limites(self):
        casos = [(-1, "Vencido"), (0, "Por vencer"), (7, "Por vencer"), (8, "Activo")]
        for dias, esperado in casos:
            with self.subTest(dias=dias):
                self.assertEqual(gimnasio.calcular_estado(dias_desde_hoy(dias)), esperado)


class TestEstadoCanceladoYCongelado(unittest.TestCase):  # REGLAS 2, 8 y 9
    def test_el_cancelado_tiene_prioridad(self):
        self.assertEqual(
            gimnasio.calcular_estado(dias_desde_hoy(20), date.today(), True), "Cancelado"
        )

    def test_el_congelado_va_antes_que_vencido(self):
        self.assertEqual(gimnasio.calcular_estado(dias_desde_hoy(-1), None, True), "Congelado")

    def test_sin_cancelar_ni_congelar_sigue_por_fechas(self):
        self.assertEqual(gimnasio.calcular_estado(dias_desde_hoy(20), None, False), "Activo")


class TestDiasNoUsados(unittest.TestCase):  # REGLA 9
    def test_casos(self):
        casos = [(dias_desde_hoy(5), 5), (date.today(), 0), (dias_desde_hoy(-2), 0)]
        for fecha, esperado in casos:
            with self.subTest(fecha=fecha):
                self.assertEqual(gimnasio.calcular_dias_no_usados(fecha), esperado)


class TestImc(unittest.TestCase):  # REGLA 4
    def test_limites_de_categoria(self):
        # Con altura 1 m, el IMC es igual al peso
        casos = [
            (18.49, "Bajo peso"),
            (18.5, "Normal"),
            (24.99, "Normal"),
            (25, "Sobrepeso"),
            (29.99, "Sobrepeso"),
            (30, "Obesidad"),
        ]
        for peso, esperado in casos:
            with self.subTest(peso=peso):
                self.assertEqual(gimnasio.calcular_imc(peso, 1), (peso, esperado))

    def test_la_categoria_se_elige_antes_de_redondear(self):
        # 24.996 se muestra como 25.0, pero sigue siendo Normal
        self.assertEqual(gimnasio.calcular_imc(24.996, 1), (25.0, "Normal"))


class TestProgreso(unittest.TestCase):  # REGLA 6
    def test_casos(self):
        casos = [
            ("bajar peso", 72, 68, -4, "Va bien"),
            ("bajar peso", 72, 72, 0, "No va bien"),
            ("ganar musculo", 70, 71, 1, "Va bien"),
            ("ganar musculo", 70, 70, 0, "No va bien"),
            ("mantenerse", 80, 82, 2, "Va bien"),
            ("mantenerse", 80, 78, -2, "Va bien"),
            ("mantenerse", 80, 82.1, 2.1, "No va bien"),
        ]
        for objetivo, inicial, actual, diferencia, resultado in casos:
            with self.subTest(objetivo=objetivo, actual=actual):
                self.assertEqual(
                    gimnasio.calcular_progreso(objetivo, inicial, actual),
                    (diferencia, resultado),
                )


class TestRutinaPorDia(unittest.TestCase):  # REGLAS 11 a 14
    def test_siguiente_dia(self):
        casos = [(None, 1), (1, 2), (2, 3), (3, 1)]
        for ultimo, esperado in casos:
            with self.subTest(ultimo=ultimo):
                self.assertEqual(gimnasio.calcular_siguiente_dia(ultimo), esperado)

    def test_cumplimiento(self):
        self.assertEqual(gimnasio.calcular_cumplimiento(0, 0), 0)
        self.assertEqual(gimnasio.calcular_cumplimiento(2, 3), 67)
        self.assertEqual(gimnasio.calcular_cumplimiento(3, 3), 100)

    def test_asistencia(self):
        casos = [
            (6, 3, 50),    # plan de 3 días: se esperan 12
            (12, 3, 100),
            (6, 7, 50),    # plan libre: se esperan 12, no 28
            (28, 7, 100),  # nunca pasa de 100
            (0, 3, 0),
        ]
        for entradas, dias_por_semana, esperado in casos:
            with self.subTest(entradas=entradas, dias=dias_por_semana):
                self.assertEqual(gimnasio.calcular_asistencia(entradas, dias_por_semana), esperado)

    def test_nivel_sugerido(self):
        casos = [
            ("principiante", 8, 80, "intermedio"),
            ("intermedio", 8, 80, "avanzado"),
            ("avanzado", 12, 100, None),
            ("principiante", 7, 100, None),
            ("principiante", 8, 79, None),
            ("viejo", 8, 100, None),
        ]
        for nivel, entradas, cumplimiento, esperado in casos:
            with self.subTest(nivel=nivel, entradas=entradas, cumplimiento=cumplimiento):
                self.assertEqual(
                    gimnasio.calcular_nivel_sugerido(nivel, entradas, cumplimiento), esperado
                )


class TestLeerNumeros(unittest.TestCase):
    def test_numeros_validos(self):
        self.assertEqual(gimnasio.leer_numero("1.75"), 1.75)
        self.assertEqual(gimnasio.leer_numero(68), 68)

    def test_numeros_invalidos(self):
        for valor in ["abc", "", None, True, "nan", "inf", [], {}]:
            with self.subTest(valor=valor):
                self.assertIsNone(gimnasio.leer_numero(valor))

    def test_enteros(self):
        self.assertEqual(gimnasio.leer_entero("3"), 3)
        self.assertIsNone(gimnasio.leer_entero("1.5"))
        self.assertIsNone(gimnasio.leer_entero("abc"))


class TestValidarSocio(unittest.TestCase):
    def test_datos_correctos(self):
        self.assertIsNone(gimnasio.validar_datos_socio(socio_valido(), CAMPOS_ALTA))

    def test_campo_faltante_o_vacio(self):
        for valor in [None, "", "   "]:
            with self.subTest(valor=valor):
                mensaje = gimnasio.validar_datos_socio(socio_valido(nombre=valor), CAMPOS_ALTA)
                self.assertEqual(mensaje, "Falta el campo: nombre")

    def test_valores_invalidos(self):
        casos = [
            ({"objetivo": "volar"}, "El objetivo no es válido"),
            ({"nivel": "experto"}, "El nivel no es válido"),
            ({"altura": "abc"}, "La altura debe estar en metros (ej: 1.75)"),
            ({"altura": "0.4"}, "La altura debe estar en metros (ej: 1.75)"),
            ({"altura": "2.51"}, "La altura debe estar en metros (ej: 1.75)"),
            ({"peso": "abc"}, "El peso debe estar entre 1 y 500 kg"),
            ({"peso": "-5"}, "El peso debe estar entre 1 y 500 kg"),
            ({"peso": "501"}, "El peso debe estar entre 1 y 500 kg"),
            ({"plan_id": "abc"}, "El plan no es válido"),
            ({"nombre": "a" * 101}, "El campo nombre admite hasta 100 caracteres"),
            ({"ci": 123}, "El campo ci debe ser texto"),
        ]
        for cambios, esperado in casos:
            with self.subTest(cambios=cambios):
                self.assertEqual(
                    gimnasio.validar_datos_socio(socio_valido(**cambios), CAMPOS_ALTA),
                    esperado,
                )

    def test_limites_validos(self):
        for cambios in [{"altura": "0.5"}, {"altura": "2.5"}, {"peso": "1"}, {"peso": "500"}]:
            with self.subTest(cambios=cambios):
                self.assertIsNone(gimnasio.validar_datos_socio(socio_valido(**cambios), CAMPOS_ALTA))

    def test_el_telefono_es_opcional(self):
        self.assertIsNone(gimnasio.validar_datos_socio(socio_valido(telefono=None), CAMPOS_ALTA))


class TestRutas(unittest.TestCase):
    # La validación ocurre antes de usar la base, así que no hace falta MySQL.
    # Lo único que se simula es el usuario de la sesión.
    def setUp(self):
        self.cliente = gimnasio.app.test_client()
        with self.cliente.session_transaction() as sesion:
            sesion["usuario_id"] = 1
        admin = {"id": 1, "nombre": "Admin", "usuario": "admin", "rol": "admin"}
        simulacion = patch.object(gimnasio, "consultar_uno", return_value=admin)
        simulacion.start()
        self.addCleanup(simulacion.stop)

    def test_alta_con_numero_invalido_devuelve_400(self):
        respuesta = self.cliente.post("/api/socios", json=socio_valido(peso="abc"))
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.get_json()["error"], "El peso debe estar entre 1 y 500 kg")

    def test_alta_con_cuerpo_invalido_devuelve_400(self):
        for cuerpo in ["", "esto no es json", "[1, 2]"]:
            with self.subTest(cuerpo=cuerpo):
                respuesta = self.cliente.post(
                    "/api/socios", data=cuerpo, content_type="application/json"
                )
                self.assertEqual(respuesta.status_code, 400)
                self.assertEqual(respuesta.get_json()["error"], "Falta el campo: nombre")


class TestBusqueda(unittest.TestCase):  # T2: sesión simulada, sin MySQL
    def setUp(self):
        self.cliente = gimnasio.app.test_client()
        with self.cliente.session_transaction() as sesion:
            sesion["usuario_id"] = 1
        admin = {"id": 1, "nombre": "Admin", "usuario": "admin", "rol": "admin"}
        simulacion = patch.object(gimnasio, "consultar_uno", return_value=admin)
        simulacion.start()
        self.addCleanup(simulacion.stop)
        self.socios = []
        casos = [(20, None, False), (7, None, False), (-1, None, False),
                 (-1, None, True), (20, date.today(), True)]
        for i, (dias, cancelacion, congelado) in enumerate(casos, 1):
            self.socios.append({
                "id": i, "nombre": "Ana " + str(i), "ci": str(i), "plan": "Mensual",
                "fecha_vencimiento": dias_desde_hoy(dias),
                "fecha_cancelacion": cancelacion, "congelado": congelado,
            })

    def test_sin_filtros_oculta_solo_cancelados(self):
        with patch.object(gimnasio, "consultar", return_value=self.socios):
            respuesta = self.cliente.get("/api/socios")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual([s["id"] for s in respuesta.get_json()], [1, 2, 3, 4])

    def test_cada_estado_y_su_prioridad(self):
        for i, estado in enumerate(["Activo", "Por vencer", "Vencido", "Congelado", "Cancelado"], 1):
            with self.subTest(estado=estado):
                with patch.object(gimnasio, "consultar", return_value=self.socios):
                    respuesta = self.cliente.get("/api/socios", query_string={"estado": estado})
                self.assertEqual(respuesta.status_code, 200)
                self.assertEqual([s["id"] for s in respuesta.get_json()], [i])
                self.assertEqual(respuesta.get_json()[0]["estado"], estado)

    def test_estado_desconocido_o_vacio_devuelve_400_sin_listar(self):
        for estado in ["", "activo", "Todos", "No existe"]:
            with self.subTest(estado=estado):
                with patch.object(gimnasio, "consultar") as consulta:
                    respuesta = self.cliente.get("/api/socios", query_string={"estado": estado})
                self.assertEqual(respuesta.status_code, 400)
                self.assertEqual(respuesta.get_json()["error"], "El estado no es válido")
                consulta.assert_not_called()

    def test_busqueda_parametrizada_por_nombre_o_ci(self):
        for texto in ["Ana", "123", "' OR 1=1 --"]:
            with self.subTest(texto=texto):
                with patch.object(gimnasio, "consultar", return_value=[]) as consulta:
                    respuesta = self.cliente.get("/api/socios", query_string={"q": texto})
                self.assertEqual(respuesta.get_json(), [])
                sql, parametros = consulta.call_args.args
                self.assertIn("s.nombre LIKE %s ESCAPE '!' OR s.ci LIKE %s ESCAPE '!'", sql)
                self.assertNotIn(texto, sql)
                self.assertEqual(parametros, ("%" + texto + "%", "%" + texto + "%"))

    def test_comodines_y_escape_se_buscan_como_texto(self):
        for texto, patron in [("%", "%!%%"), ("_", "%!_%"), ("!", "%!!%"),
                              ("a!%_", "%a!!!%!_%"), (r"a\b", r"%a\b%")]:
            with self.subTest(texto=texto):
                with patch.object(gimnasio, "consultar", return_value=[]) as consulta:
                    self.cliente.get("/api/socios", query_string={"q": texto})
                self.assertEqual(consulta.call_args.args[1], (patron, patron))

    def test_busqueda_y_estado_se_combinan(self):
        # consultar devuelve las coincidencias de texto; el estado se calcula después.
        with patch.object(gimnasio, "consultar", return_value=self.socios[2:]) as consulta:
            respuesta = self.cliente.get("/api/socios", query_string={"q": "Ana", "estado": "Vencido"})
        self.assertEqual(consulta.call_args.args[1], ("%Ana%", "%Ana%"))
        self.assertEqual([s["id"] for s in respuesta.get_json()], [3])

    def test_texto_vacio_equivale_a_sin_busqueda(self):
        for texto in ["", "   "]:
            with self.subTest(texto=texto):
                with patch.object(gimnasio, "consultar", return_value=self.socios) as consulta:
                    respuesta = self.cliente.get("/api/socios", query_string={"q": texto})
                self.assertEqual(len(respuesta.get_json()), 4)
                self.assertEqual(consulta.call_args.args[1], ())
                self.assertNotIn("LIKE", consulta.call_args.args[0])


class TestRiesgo(unittest.TestCase):  # REGLA 10
    def test_cuenta_desde_la_ultima_entrada(self):
        self.assertEqual(gimnasio.calcular_dias_sin_entrar(dias_desde_hoy(-14), dias_desde_hoy(-60)), 14)

    def test_sin_entradas_cuenta_desde_el_primer_pago(self):
        self.assertEqual(gimnasio.calcular_dias_sin_entrar(None, dias_desde_hoy(-3)), 3)

    def test_sin_entradas_ni_pagos(self):
        self.assertIsNone(gimnasio.calcular_dias_sin_entrar(None, None))

    def test_limite_de_14_dias(self):
        self.assertFalse(gimnasio.esta_en_riesgo("Activo", 13))
        self.assertTrue(gimnasio.esta_en_riesgo("Activo", 14))
        self.assertTrue(gimnasio.esta_en_riesgo("Por vencer", 30))

    def test_sin_datos_esta_en_riesgo(self):
        self.assertTrue(gimnasio.esta_en_riesgo("Activo", None))

    def test_solo_planes_en_uso(self):
        for estado in ["Congelado", "Vencido", "Cancelado"]:
            with self.subTest(estado=estado):
                self.assertFalse(gimnasio.esta_en_riesgo(estado, 100))
                self.assertFalse(gimnasio.esta_en_riesgo(estado, None))


class TestPlanMasVendido(unittest.TestCase):  # T6
    def test_gana_el_de_mas_ventas(self):
        self.assertEqual(gimnasio.elegir_plan_mas_vendido({"Mensual": 2, "Anual": 5}), "Anual")

    def test_empate_por_orden_alfabetico(self):
        self.assertEqual(
            gimnasio.elegir_plan_mas_vendido({"Trimestral": 3, "Mensual": 3, "Anual": 1}), "Mensual"
        )

    def test_sin_ventas(self):
        self.assertIsNone(gimnasio.elegir_plan_mas_vendido({}))


class TestDashboard(unittest.TestCase):  # T6: sesión y consultas simuladas, sin MySQL
    def setUp(self):
        self.cliente = gimnasio.app.test_client()
        with self.cliente.session_transaction() as sesion:
            sesion["usuario_id"] = 2
        recepcion = {"id": 2, "nombre": "Recepción", "usuario": "recepcion", "rol": "recepcion"}
        simulacion = patch.object(gimnasio, "consultar_uno", return_value=recepcion)
        simulacion.start()
        self.addCleanup(simulacion.stop)

    def socio(self, id, dias, ultima=None, pago=None, cancelacion=None, congelado=False):
        return {
            "id": id, "nombre": "Socio " + str(id), "ci": str(id), "plan": "Mensual",
            "fecha_vencimiento": dias_desde_hoy(dias), "fecha_cancelacion": cancelacion,
            "congelado": congelado, "ultima_entrada": ultima, "primer_pago": pago,
        }

    def test_totales_listas_riesgo_e_ingresos(self):
        socios = [
            self.socio(1, 20, ultima=dias_desde_hoy(-2)),
            self.socio(2, 20, ultima=dias_desde_hoy(-14)),
            self.socio(3, 5, pago=dias_desde_hoy(-20)),
            self.socio(4, -1, ultima=dias_desde_hoy(-40)),
            self.socio(5, 20, congelado=True, ultima=dias_desde_hoy(-40)),
            self.socio(6, 20, cancelacion=date.today()),
            self.socio(7, 20),
        ]
        ventas = [
            {"nombre": "Trimestral", "cantidad": 2, "total": Decimal("240.00")},
            {"nombre": "Mensual", "cantidad": 2, "total": Decimal("90.50")},
        ]
        with patch.object(gimnasio, "consultar", side_effect=[socios, ventas]):
            respuesta = self.cliente.get("/api/dashboard")
        self.assertEqual(respuesta.status_code, 200)
        datos = respuesta.get_json()
        self.assertEqual(datos["totales"], [
            {"estado": "Activo", "cantidad": 3}, {"estado": "Por vencer", "cantidad": 1},
            {"estado": "Vencido", "cantidad": 1}, {"estado": "Congelado", "cantidad": 1},
            {"estado": "Cancelado", "cantidad": 1},
        ])
        self.assertEqual(datos["ingresos_mes"], 330.5)
        self.assertEqual(datos["plan_mas_vendido"], "Mensual")
        self.assertEqual(datos["ventas_plan_mas_vendido"], 2)
        self.assertEqual(
            [(lista["estado"], [s["id"] for s in lista["socios"]]) for lista in datos["listas"]],
            [("Vencido", [4]), ("Por vencer", [3]), ("Congelado", [5]), ("Cancelado", [6])],
        )
        self.assertEqual(
            [(s["id"], s["dias_sin_entrar"]) for s in datos["en_riesgo"]], [(2, 14), (3, 20), (7, None)]
        )

    def test_mes_sin_ventas(self):
        with patch.object(gimnasio, "consultar", side_effect=[[], []]) as consulta:
            datos = self.cliente.get("/api/dashboard").get_json()
        self.assertEqual(datos["ingresos_mes"], 0)
        self.assertIsNone(datos["plan_mas_vendido"])
        # El mes calendario se pasa como parámetros: del día 1 al día 1 del mes siguiente
        inicio, fin = consulta.call_args.args[1]
        self.assertEqual(inicio, date.today().replace(day=1))
        self.assertEqual(fin.day, 1)
        self.assertEqual((fin - timedelta(days=1)).month, inicio.month)


class TestPermisos(unittest.TestCase):  # REGLA 15
    def cliente_con_rol(self, rol):
        cliente = gimnasio.app.test_client()
        with cliente.session_transaction() as sesion:
            sesion["usuario_id"] = 1
        usuario = {"id": 1, "nombre": "Prueba", "usuario": "prueba", "rol": rol}
        simulacion = patch.object(gimnasio, "consultar_uno", return_value=usuario)
        simulacion.start()
        self.addCleanup(simulacion.stop)
        return cliente

    def test_sin_sesion_devuelve_401(self):
        cliente = gimnasio.app.test_client()
        for metodo, ruta in [("get", "/api/socios"), ("post", "/api/socios/1/checkin"), ("get", "/api/sesion")]:
            with self.subTest(ruta=ruta):
                self.assertEqual(getattr(cliente, metodo)(ruta).status_code, 401)

    def test_recepcion_no_usa_rutas_de_admin(self):
        cliente = self.cliente_con_rol("recepcion")
        casos = [
            ("delete", "/api/socios/1"),
            ("put", "/api/planes/1"),
            ("get", "/api/usuarios"),
            ("post", "/api/usuarios"),
            ("patch", "/api/usuarios/1"),
        ]
        for metodo, ruta in casos:
            with self.subTest(ruta=ruta):
                self.assertEqual(getattr(cliente, metodo)(ruta).status_code, 403)

    def test_paginas_estaticas_no_piden_sesion(self):
        respuesta = gimnasio.app.test_client().get("/login.html")
        self.assertEqual(respuesta.status_code, 200)
        respuesta.close()


class TestTransaccion(unittest.TestCase):
    def test_si_todo_va_bien_confirma(self):
        conexion = MagicMock()
        with patch.object(gimnasio, "conectar", return_value=conexion):
            with gimnasio.transaccion() as cursor:
                cursor.execute("INSERT ...")
        conexion.commit.assert_called_once()
        conexion.rollback.assert_not_called()
        conexion.close.assert_called_once()

    def test_si_algo_falla_deshace_todo(self):
        conexion = MagicMock()
        with patch.object(gimnasio, "conectar", return_value=conexion):
            with self.assertRaises(ValueError):
                with gimnasio.transaccion():
                    raise ValueError("falló la segunda escritura")
        conexion.commit.assert_not_called()
        conexion.rollback.assert_called_once()
        conexion.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
