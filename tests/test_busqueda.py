"""Integración T2: búsqueda de socios contra MySQL/MariaDB real.

Ejecutar: GIMNASIO_TEST_PORT=<puerto> python -m unittest tests.test_busqueda -v
"""

import unittest
from uuid import uuid4

import app as gimnasio
from tests.integracion import PruebaConBase


class TestBusquedaReal(PruebaConBase):
    def setUp(self):
        super().setUp()
        # Una marca propia evita coincidir con los socios de ejemplo
        self.marca = "Zq" + uuid4().hex[:6]
        self.activo = self.crear_socio("Activo " + self.marca)
        self.vencido = self.crear_socio("Vencido " + self.marca)
        self.cancelado = self.crear_socio("Cancelado " + self.marca)
        self.comodin = self.crear_socio("Con 50%_off! " + self.marca)
        gimnasio.ejecutar(
            "UPDATE socios SET fecha_vencimiento = CURDATE() - INTERVAL 1 DAY WHERE id = %s",
            (self.vencido,),
        )
        self.assertEqual(self.cliente.post(f"/api/socios/{self.cancelado}/cancelar").status_code, 200)

    def buscar(self, **parametros):
        respuesta = self.cliente.get("/api/socios", query_string=parametros)
        self.assertEqual(respuesta.status_code, 200)
        return [socio["id"] for socio in respuesta.get_json()]

    def test_coincidencia_parcial_sin_mayusculas_ni_cancelados(self):
        self.assertEqual(
            sorted(self.buscar(q=self.marca.upper())),
            sorted([self.activo, self.vencido, self.comodin]),
        )

    def test_busca_por_ci_parcial(self):
        ci = self.ficha(self.vencido)["ci"]
        self.assertEqual(self.buscar(q=ci[3:12]), [self.vencido])

    def test_combina_texto_y_estado(self):
        self.assertEqual(self.buscar(q=self.marca, estado="Vencido"), [self.vencido])
        self.assertEqual(self.buscar(q=self.marca, estado="Cancelado"), [self.cancelado])
        self.assertEqual(self.buscar(q=self.marca, estado="Congelado"), [])

    def test_comodines_de_like_son_texto(self):
        self.assertEqual(self.buscar(q="50%_off!"), [self.comodin])
        self.assertEqual(self.buscar(q="5_%" + self.marca), [])

    def test_inyeccion_no_devuelve_otros_socios(self):
        self.assertEqual(self.buscar(q="' OR 1=1 -- " + self.marca), [])

    def test_estado_invalido_devuelve_400(self):
        respuesta = self.cliente.get("/api/socios", query_string={"estado": "Moroso"})
        self.assertEqual(respuesta.status_code, 400)


if __name__ == "__main__":
    unittest.main()
