"""Capa de dispositivos IoT: sensores simulados de energía, movilidad y residuos."""
import random
import time


class Sensor:
    def __init__(self, sensor_id, dominio, zona, semilla=None):
        self.id = sensor_id
        self.dominio = dominio          # "energia", "movilidad" o "residuos"
        self.zona = zona
        self._rnd = random.Random(semilla)
        self._nivel = self._rnd.uniform(10, 50)   # solo para residuos

    def leer(self):
        """Devuelve una lectura. A veces produce un valor inválido, como un sensor real."""
        if self._rnd.random() < 0.03:
            valor = -1.0                                   # lectura errónea
        elif self.dominio == "energia":
            valor = round(self._rnd.uniform(0.08, 0.15), 3)  # kWh de una luminaria
        elif self.dominio == "movilidad":
            valor = float(self._rnd.randint(5, 60))          # vehículos por minuto
        else:
            self._nivel = min(100.0, self._nivel + self._rnd.uniform(0, 4))
            valor = round(self._nivel, 1)                    # % de llenado
        return {"sensor": self.id, "dominio": self.dominio, "zona": self.zona,
                "valor": valor, "ts": time.time()}

    def vaciar(self):
        """El camión recogió el contenedor."""
        self._nivel = 0.0
