"""Base de las pruebas de integración sobre un servidor exclusivo.

GIMNASIO_TEST_PORT debe indicar el puerto del servidor aislado (nunca 3306),
con base_datos.sql ya importado. Las pruebas crean socios propios y los
eliminan al terminar.
"""

import os
import unittest
from uuid import uuid4
from unittest.mock import patch

import mysql.connector

import app as gimnasio


@unittest.skipUnless(os.environ.get("GIMNASIO_TEST_PORT"), "Requiere servidor aislado")
class PruebaConBase(unittest.TestCase):
    usuario = "admin"
    clave = "admin1234"

    def setUp(self):
        puerto = int(os.environ["GIMNASIO_TEST_PORT"])
        if puerto == 3306:
            self.fail("No se permiten pruebas de integración en el puerto 3306")

        def conectar_prueba():
            return mysql.connector.connect(
                host="127.0.0.1", port=puerto, user="root", password="",
                database="gimnasio", use_pure=True,
            )

        simulacion = patch.object(gimnasio, "conectar", conectar_prueba)
        simulacion.start()
        self.addCleanup(simulacion.stop)
        self.cliente = gimnasio.app.test_client()
        self.iniciar_sesion(self.usuario, self.clave)

    def iniciar_sesion(self, usuario, clave):
        respuesta = self.cliente.post("/api/login", json={"usuario": usuario, "clave": clave})
        self.assertEqual(respuesta.status_code, 200)

    def crear_socio(self, nombre="Prueba", **cambios):
        # Crea un socio por la API y lo elimina al terminar la prueba
        datos = {
            "nombre": nombre, "ci": uuid4().hex[:20], "peso": 70, "altura": 1.7,
            "objetivo": "mantenerse", "nivel": "principiante", "plan_id": 1,
        }
        datos.update(cambios)
        respuesta = self.cliente.post("/api/socios", json=datos)
        self.assertEqual(respuesta.status_code, 200, respuesta.get_json())
        socio_id = respuesta.get_json()["id"]
        self.addCleanup(self.eliminar_socio, socio_id)
        return socio_id

    def eliminar_socio(self, socio_id):
        # Con un administrador nuevo: la prueba pudo cerrar o cambiar la sesión
        cliente = gimnasio.app.test_client()
        cliente.post("/api/login", json={"usuario": "admin", "clave": "admin1234"})
        cliente.delete(f"/api/socios/{socio_id}")

    def ficha(self, socio_id):
        respuesta = self.cliente.get(f"/api/socios/{socio_id}")
        self.assertEqual(respuesta.status_code, 200)
        return respuesta.get_json()
