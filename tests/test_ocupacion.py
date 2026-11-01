"""Integración T10: salida y ocupación contra MySQL/MariaDB real.

Ejecutar: GIMNASIO_TEST_PORT=<puerto> python -m unittest tests.test_ocupacion -v
"""

import unittest

import app as gimnasio
from tests.integracion import PruebaConBase


class TestOcupacionReal(PruebaConBase):
    def adentro_ahora(self):
        respuesta = self.cliente.get("/api/dashboard")
        self.assertEqual(respuesta.status_code, 200)
        datos = respuesta.get_json()
        self.assertEqual(datos["aforo"], gimnasio.AFORO)
        return datos["adentro_ahora"]

    def adentro_en_listado(self, socio_id):
        for socio in self.cliente.get("/api/socios").get_json():
            if socio["id"] == socio_id:
                return socio["adentro"]

    def salida(self, socio_id):
        return self.cliente.post(f"/api/socios/{socio_id}/salida")

    def test_entrar_suma_y_salir_resta(self):
        socio_id = self.crear_socio("Ocupación")
        antes = self.adentro_ahora()

        self.assertEqual(self.cliente.post(f"/api/socios/{socio_id}/checkin").status_code, 200)
        self.assertEqual(self.adentro_ahora(), antes + 1)
        self.assertTrue(self.adentro_en_listado(socio_id))

        self.assertEqual(self.salida(socio_id).status_code, 200)
        self.assertEqual(self.adentro_ahora(), antes)
        self.assertFalse(self.adentro_en_listado(socio_id))

    def test_salir_sin_estar_adentro_devuelve_400(self):
        socio_id = self.crear_socio("Sin entrar")
        self.assertEqual(self.salida(socio_id).status_code, 400)

        self.cliente.post(f"/api/socios/{socio_id}/checkin")
        self.salida(socio_id)
        self.assertEqual(self.salida(socio_id).status_code, 400)

    def test_entrada_de_ayer_sin_salida_no_cuenta(self):
        socio_id = self.crear_socio("Se olvidó de salir")
        antes = self.adentro_ahora()
        gimnasio.ejecutar(
            "INSERT INTO asistencias (socio_id, fecha_hora) VALUES (%s, NOW() - INTERVAL 1 DAY)",
            (socio_id,),
        )
        self.assertEqual(self.adentro_ahora(), antes)
        self.assertEqual(self.salida(socio_id).status_code, 400)

    def test_socio_inexistente_devuelve_404(self):
        self.assertEqual(self.salida(999999).status_code, 404)


if __name__ == "__main__":
    unittest.main()
