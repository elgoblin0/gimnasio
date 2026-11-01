"""Integración T6: dashboard contra MySQL/MariaDB real.

Ejecutar: GIMNASIO_TEST_PORT=<puerto> python -m unittest tests.test_dashboard -v
"""

import unittest

import app as gimnasio
from tests.integracion import PruebaConBase


class TestDashboardReal(PruebaConBase):
    def dashboard(self):
        respuesta = self.cliente.get("/api/dashboard")
        self.assertEqual(respuesta.status_code, 200)
        return respuesta.get_json()

    def entrada_hace(self, socio_id, dias):
        gimnasio.ejecutar(
            "INSERT INTO asistencias (socio_id, fecha_hora) VALUES (%s, NOW() - INTERVAL %s DAY)",
            (socio_id, dias),
        )

    def pago_hace(self, socio_id, dias):
        gimnasio.ejecutar("UPDATE pagos SET fecha = CURDATE() - INTERVAL %s DAY WHERE socio_id = %s",
                          (dias, socio_id))

    def lista(self, estado):
        for lista in self.dashboard()["listas"]:
            if lista["estado"] == estado:
                return [socio["id"] for socio in lista["socios"]]

    def activos(self):
        return self.dashboard()["totales"][0]["cantidad"]

    def ids_en_riesgo(self):
        return {socio["id"]: socio["dias_sin_entrar"] for socio in self.dashboard()["en_riesgo"]}

    def test_regla_10_con_entradas_y_pagos_reales(self):
        recien = self.crear_socio("Recién llegado")
        hace_14 = self.crear_socio("Entró hace 14")
        hace_13 = self.crear_socio("Entró hace 13")
        sin_entrar = self.crear_socio("Pagó hace 20")
        congelado = self.crear_socio("Congelado")
        self.entrada_hace(hace_14, 14)
        self.entrada_hace(hace_13, 13)
        self.pago_hace(sin_entrar, 20)
        self.entrada_hace(congelado, 30)
        self.assertEqual(self.cliente.post(f"/api/socios/{congelado}/congelar", json={"dias": 5}).status_code, 200)

        riesgo = self.ids_en_riesgo()
        self.assertEqual(riesgo.get(hace_14), 14)
        self.assertEqual(riesgo.get(sin_entrar), 20)
        for socio_id in (recien, hace_13, congelado):
            self.assertNotIn(socio_id, riesgo)

        self.assertIn(congelado, self.lista("Congelado"))

    def test_totales_e_ingresos_cuentan_los_pagos_del_mes(self):
        antes = self.dashboard()
        activos = self.activos()
        precio = gimnasio.consultar_uno("SELECT precio FROM planes WHERE id = 2")["precio"]
        socio_id = self.crear_socio("Paga este mes", plan_id=2)
        despues = self.dashboard()
        self.assertEqual(self.activos(), activos + 1)
        self.assertAlmostEqual(despues["ingresos_mes"], antes["ingresos_mes"] + float(precio), places=2)

        # Un pago del mes anterior no cuenta
        gimnasio.ejecutar(
            "UPDATE pagos SET fecha = DATE_FORMAT(CURDATE(), '%Y-%m-01') - INTERVAL 1 DAY WHERE socio_id = %s",
            (socio_id,),
        )
        self.assertAlmostEqual(self.dashboard()["ingresos_mes"], antes["ingresos_mes"], places=2)

    def test_cancelado_sale_de_activos_y_aparece_en_su_lista(self):
        socio_id = self.crear_socio("Se da de baja")
        self.assertEqual(self.cliente.post(f"/api/socios/{socio_id}/cancelar").status_code, 200)
        self.assertIn(socio_id, self.lista("Cancelado"))
        self.assertNotIn(socio_id, self.ids_en_riesgo())

    def test_recepcion_puede_verlo(self):
        self.cliente.post("/api/logout")
        self.iniciar_sesion("recepcion", "recepcion1234")
        self.assertEqual(self.cliente.get("/api/dashboard").status_code, 200)


if __name__ == "__main__":
    unittest.main()
