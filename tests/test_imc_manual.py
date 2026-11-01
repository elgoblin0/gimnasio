"""Integración T9: IMC manual contra MySQL/MariaDB real.

Ejecutar: GIMNASIO_TEST_PORT=<puerto> python -m unittest tests.test_imc_manual -v
"""

import unittest

from tests.integracion import PruebaConBase


class TestImcManualReal(PruebaConBase):
    def setUp(self):
        super().setUp()
        # 81 kg y 1.78 m: el IMC calculado es 25.56 (Sobrepeso)
        self.socio_id = self.crear_socio("IMC manual", peso=81, altura=1.78)

    def guardar(self, imc):
        return self.cliente.put(f"/api/socios/{self.socio_id}/imc", json={"imc": imc})

    def editar(self, **cambios):
        ficha = self.ficha(self.socio_id)
        datos = {campo: ficha[campo] for campo in ("nombre", "ci", "telefono", "altura", "objetivo", "nivel")}
        datos.update(cambios)
        respuesta = self.cliente.put(f"/api/socios/{self.socio_id}", json=datos)
        self.assertEqual(respuesta.status_code, 200)

    def test_guardar_reemplaza_al_calculado_y_se_indica_manual(self):
        self.assertEqual(self.guardar(24.8).status_code, 200)
        ficha = self.ficha(self.socio_id)
        self.assertEqual((ficha["imc"], ficha["categoria_imc"], ficha["imc_manual"]), (24.8, "Normal", True))

    def test_fuera_de_rango_devuelve_400(self):
        for valor in [9.99, 70.01, "abc"]:
            with self.subTest(valor=valor):
                self.assertEqual(self.guardar(valor).status_code, 400)
        self.assertFalse(self.ficha(self.socio_id)["imc_manual"])

    def test_recepcion_recibe_403(self):
        self.cliente.post("/api/logout")
        self.iniciar_sesion("recepcion", "recepcion1234")
        self.assertEqual(self.guardar(24.8).status_code, 403)
        self.assertEqual(self.cliente.delete(f"/api/socios/{self.socio_id}/imc").status_code, 403)

    def test_peso_nuevo_lo_borra(self):
        self.guardar(24.8)
        self.assertEqual(self.cliente.post(f"/api/socios/{self.socio_id}/peso", json={"peso": 80}).status_code, 200)
        ficha = self.ficha(self.socio_id)
        self.assertFalse(ficha["imc_manual"])
        self.assertEqual(ficha["imc"], 25.25)

    def test_cambiar_la_altura_lo_borra_y_otros_datos_no(self):
        self.guardar(24.8)
        self.editar(telefono="099123456", altura="1.780")
        self.assertTrue(self.ficha(self.socio_id)["imc_manual"])
        self.editar(altura=1.80)
        self.assertFalse(self.ficha(self.socio_id)["imc_manual"])

    def test_volver_al_calculado(self):
        self.guardar(24.8)
        self.assertEqual(self.cliente.delete(f"/api/socios/{self.socio_id}/imc").status_code, 200)
        ficha = self.ficha(self.socio_id)
        self.assertEqual((ficha["imc"], ficha["categoria_imc"], ficha["imc_manual"]), (25.56, "Sobrepeso", False))


if __name__ == "__main__":
    unittest.main()
