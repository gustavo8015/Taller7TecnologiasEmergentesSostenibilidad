import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from nube import ServicioAnalitica, construir_nube
from pasarela import Pasarela


def lectura(valor, dominio="energia", sensor="s1"):
    return {"sensor": sensor, "dominio": dominio, "zona": "Centro", "valor": valor, "ts": 0.0}


class PruebasPasarela(unittest.TestCase):
    def setUp(self):
        self.enviados = []
        self.pasarela = Pasarela("Centro", self.enviados.append, ventana=5)

    def test_descarta_lecturas_fuera_de_rango(self):
        self.pasarela.recibir(lectura(-1.0))
        self.assertEqual(self.pasarela.descartadas, 1)
        self.assertEqual(self.enviados, [])

    def test_agrega_cinco_lecturas_en_un_mensaje(self):
        for valor in (1, 2, 3, 4, 5):
            self.pasarela.recibir(lectura(float(valor)))
        self.assertEqual(len(self.enviados), 1)
        self.assertEqual(self.enviados[0]["valor"], 3.0)
        self.assertEqual(self.enviados[0]["muestras"], 5)

    def test_alerta_inmediata_y_unica_por_contenedor_lleno(self):
        self.pasarela.recibir(lectura(85.0, "residuos"))
        self.pasarela.recibir(lectura(90.0, "residuos"))
        alertas = [m for m in self.enviados if m["tipo"] == "alerta"]
        self.assertEqual(len(alertas), 1)

    def test_guarda_en_bufer_sin_enlace_y_envia_al_reconectar(self):
        self.pasarela.enlace_activo = False
        for valor in (1, 2, 3, 4, 5):
            self.pasarela.recibir(lectura(float(valor)))
        self.assertEqual(self.enviados, [])
        self.assertEqual(self.pasarela.en_bufer, 1)
        self.assertEqual(self.pasarela.reconectar(), 1)
        self.assertEqual(len(self.enviados), 1)
        self.assertEqual(self.pasarela.en_bufer, 0)


class PruebasNube(unittest.TestCase):
    def test_flujo_completo_guarda_medicion_alerta_y_pronostico(self):
        avisos = []
        ingesta, almacen = construir_nube(avisar=avisos.append)
        pasarela = Pasarela("Centro", ingesta.recibir, ventana=2)
        for valor in (70.0, 74.0, 82.0, 86.0):
            pasarela.recibir(lectura(valor, "residuos", "res-1"))
        ingesta.cerrar()
        self.assertEqual(almacen.ejecutar("SELECT COUNT(*) FROM mediciones")[0][0], 2)
        self.assertEqual(almacen.ejecutar("SELECT COUNT(*) FROM alertas")[0][0], 1)
        self.assertEqual(len(avisos), 1)
        self.assertIn("se llena", almacen.ejecutar("SELECT detalle FROM pronosticos")[0][0])

    def test_resumen_del_tablero(self):
        from api import resumen
        ingesta, almacen = construir_nube(avisar=lambda _: None)
        pasarela = Pasarela("Centro", ingesta.recibir, ventana=2)
        for valor in (70.0, 74.0, 82.0, 86.0):
            pasarela.recibir(lectura(valor, "residuos", "res-1"))
        pasarela.recibir(lectura(-1.0))
        ingesta.cerrar()
        datos = resumen(almacen, [pasarela])
        self.assertEqual(datos["borde"]["recibidas"], 5)
        self.assertEqual(datos["borde"]["descartadas"], 1)
        self.assertEqual(datos["pasarelas"][0]["zona"], "Centro")
        self.assertTrue(datos["pasarelas"][0]["enlace"])
        self.assertEqual(datos["contenedores"][0][:3], ("res-1", "Centro", 84.0))
        self.assertEqual(datos["promedios"][0][:2], ("residuos", "Centro"))

    def test_pronostico_de_llenado(self):
        valor, detalle = ServicioAnalitica.pronosticar([60.0, 70.0, 80.0], "residuos")
        self.assertEqual(valor, 90.0)
        self.assertEqual(detalle, "se llena en unas 2 ventanas")

    def test_pronostico_media_movil(self):
        self.assertEqual(ServicioAnalitica.pronosticar([10.0, 20.0], "movilidad"), (15.0, "media móvil"))


if __name__ == "__main__":
    unittest.main()
