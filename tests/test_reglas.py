# =============================================
# Pruebas de las reglas del gimnasio
# No hacen falta MySQL ni librerías nuevas.
# Ejecutar desde la carpeta del proyecto con:
#   python3 -m unittest tests.test_reglas
# =============================================

import unittest
from datetime import date, timedelta
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
    # La validación ocurre antes de usar la base, así que no hace falta MySQL
    def setUp(self):
        self.cliente = gimnasio.app.test_client()

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
