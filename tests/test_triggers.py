"""Integración T4 sobre una base de ejemplo en un servidor exclusivo.

GIMNASIO_TEST_PORT debe indicar el puerto del servidor aislado (nunca 3306).
No importa base_datos.sql ni borra la base. Crea y elimina socios de prueba
y reemplaza los triggers al comprobar la repetición de la migración.
Ejecutar: python -m unittest tests.test_triggers -v
"""

import os
import unittest
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch

import mysql.connector

import app as gimnasio


@unittest.skipUnless(os.environ.get("GIMNASIO_TEST_PORT"), "Requiere servidor aislado")
class TestTriggers(unittest.TestCase):
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
        respuesta = self.cliente.post("/api/login", json={"usuario": "admin", "clave": "admin1234"})
        self.assertEqual(respuesta.status_code, 200)
        respuesta = self.cliente.post("/api/socios", json={
            "nombre": "Prueba T4", "ci": uuid4().hex[:20], "peso": 70,
            "altura": 1.7, "objetivo": "mantenerse", "nivel": "principiante", "plan_id": 1,
        })
        self.assertEqual(respuesta.status_code, 200)
        self.socio_id = respuesta.get_json()["id"]
        self.addCleanup(self.eliminar_prueba)

    def eliminar_prueba(self):
        self.cliente.delete(f"/api/socios/{self.socio_id}")

    def ficha(self):
        respuesta = self.cliente.get(f"/api/socios/{self.socio_id}")
        self.assertEqual(respuesta.status_code, 200)
        return respuesta.get_json()

    def test_insertar_peso_directamente_lo_copia_sin_auditar(self):
        gimnasio.ejecutar(
            "INSERT INTO registros_peso (socio_id, fecha, peso) VALUES (%s, CURDATE(), %s)",
            (self.socio_id, 72.5),
        )
        self.assertEqual(self.ficha()["peso"], 72.5)
        self.assertEqual(self.ficha()["auditoria"], [])

    def test_audita_solo_plan_solo_vencimiento_y_ambos(self):
        anterior = self.ficha()["fecha_vencimiento"]
        gimnasio.ejecutar("UPDATE socios SET plan_id = 2 WHERE id = %s", (self.socio_id,))
        gimnasio.ejecutar(
            "UPDATE socios SET fecha_vencimiento = fecha_vencimiento + INTERVAL 1 DAY WHERE id = %s",
            (self.socio_id,),
        )
        self.assertEqual(self.cliente.post(
            f"/api/socios/{self.socio_id}/renovar", json={"plan_id": 3}
        ).status_code, 200)
        cambios = self.ficha()["auditoria"]
        self.assertEqual(len(cambios), 3)
        # Los cambios del mismo segundo también quedan del más reciente al más antiguo.
        self.assertEqual((cambios[0]["plan_anterior"], cambios[0]["plan_nuevo"]), (2, 3))
        self.assertEqual((cambios[1]["plan_anterior"], cambios[1]["plan_nuevo"]), (2, 2))
        self.assertEqual(cambios[2]["vencimiento_anterior"], anterior)
        self.assertEqual(cambios[2]["vencimiento_nuevo"], anterior)
        self.assertEqual((cambios[2]["plan_anterior"], cambios[2]["plan_nuevo"]), (1, 2))
        self.assertEqual(cambios[0]["nombre_plan_nuevo"], "Trimestral")
        self.assertTrue(cambios[0]["fecha_hora"])

    def test_no_audita_valores_iguales_ni_otros_campos(self):
        gimnasio.ejecutar(
            "UPDATE socios SET plan_id = plan_id, fecha_vencimiento = fecha_vencimiento, "
            "nombre = 'Otro nombre' WHERE id = %s", (self.socio_id,),
        )
        self.assertEqual(self.ficha()["auditoria"], [])

    def test_repetir_migracion_conserva_historial_y_triggers(self):
        gimnasio.ejecutar("UPDATE socios SET plan_id = 2 WHERE id = %s", (self.socio_id,))
        anterior = self.ficha()["auditoria"]
        migracion = (Path(__file__).resolve().parents[1] / "migraciones/004_triggers.sql").read_text(
            encoding="utf-8"
        )
        # Los triggers tienen una sola sentencia, sin bloques ni DELIMITER.
        for _ in range(2):
            with gimnasio.transaccion() as cursor:
                for sentencia in migracion.split(";"):
                    if sentencia.strip():
                        cursor.execute(sentencia)
        self.assertEqual(self.ficha()["auditoria"], anterior)
        gimnasio.ejecutar(
            "INSERT INTO registros_peso (socio_id, fecha, peso) VALUES (%s, CURDATE(), 75)",
            (self.socio_id,),
        )
        gimnasio.ejecutar("UPDATE socios SET plan_id = 1 WHERE id = %s", (self.socio_id,))
        self.assertEqual(self.ficha()["peso"], 75)
        self.assertEqual(len(self.ficha()["auditoria"]), 2)

    def test_congelar_y_descongelar_quedan_auditados(self):
        anterior = self.ficha()["fecha_vencimiento"]
        nuevo = str(date.fromisoformat(anterior) + timedelta(days=7))
        self.assertEqual(self.cliente.post(
            f"/api/socios/{self.socio_id}/congelar", json={"dias": 7}
        ).status_code, 200)
        ficha = self.ficha()
        self.assertEqual(ficha["estado"], "Congelado")
        self.assertEqual(ficha["fecha_vencimiento"], nuevo)
        self.assertEqual(len(ficha["auditoria"]), 1)
        self.assertEqual(self.cliente.post(f"/api/socios/{self.socio_id}/descongelar").status_code, 200)
        ficha = self.ficha()
        self.assertEqual(ficha["fecha_vencimiento"], anterior)
        self.assertEqual(len(ficha["auditoria"]), 2)
        self.assertEqual(ficha["auditoria"][0]["vencimiento_anterior"], nuevo)
        self.assertEqual(ficha["auditoria"][0]["vencimiento_nuevo"], anterior)
        self.assertEqual(ficha["auditoria"][1]["vencimiento_anterior"], anterior)
        self.assertEqual(ficha["auditoria"][1]["vencimiento_nuevo"], nuevo)

    def test_rollback_deshace_el_peso_y_la_auditoria(self):
        with self.assertRaises(ValueError):
            with gimnasio.transaccion() as cursor:
                cursor.execute(
                    "INSERT INTO registros_peso (socio_id, fecha, peso) VALUES (%s, CURDATE(), 80)",
                    (self.socio_id,),
                )
                cursor.execute("UPDATE socios SET plan_id = 2 WHERE id = %s", (self.socio_id,))
                raise ValueError("Fallo posterior al trigger")
        ficha = self.ficha()
        self.assertEqual(ficha["peso"], 70)
        self.assertEqual(len(ficha["historial_peso"]), 1)
        self.assertEqual(ficha["auditoria"], [])

    def test_api_peso_y_eliminar_socio_con_auditoria(self):
        self.assertEqual(self.cliente.post(
            f"/api/socios/{self.socio_id}/peso", json={"peso": 73}
        ).status_code, 200)
        self.assertEqual(self.ficha()["peso"], 73)
        gimnasio.ejecutar("UPDATE socios SET plan_id = 2 WHERE id = %s", (self.socio_id,))
        self.assertEqual(len(self.ficha()["auditoria"]), 1)
        self.assertEqual(self.cliente.delete(f"/api/socios/{self.socio_id}").status_code, 200)
        self.assertFalse(gimnasio.socio_existe(self.socio_id))
        self.assertEqual(gimnasio.consultar(
            "SELECT id FROM auditoria_socios WHERE socio_id = %s", (self.socio_id,),
        ), [])


if __name__ == "__main__":
    unittest.main()
