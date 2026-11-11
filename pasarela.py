"""Capa Edge Computing: valida, filtra, agrega y aplica reglas locales."""
from collections import defaultdict

RANGOS = {"energia": (0.0, 5.0), "movilidad": (0.0, 500.0), "residuos": (0.0, 100.0)}
UMBRAL_LLENADO = 80.0


class Pasarela:
    def __init__(self, zona, enviar, ventana=5):
        self.zona = zona
        self._enviar = enviar            # función que entrega un mensaje a la nube
        self.ventana = ventana           # lecturas por sensor antes de enviar un promedio
        self.enlace_activo = True
        self._pendientes = defaultdict(list)
        self._bufer = []                 # mensajes guardados mientras no hay enlace
        self._alertados = set()
        self.recibidas = 0
        self.descartadas = 0
        self.enviadas = 0

    def recibir(self, lectura):
        self.recibidas += 1
        minimo, maximo = RANGOS[lectura["dominio"]]
        if not minimo <= lectura["valor"] <= maximo:
            self.descartadas += 1        # validación: fuera de rango
            return
        # Regla local: un contenedor casi lleno se avisa de inmediato, sin esperar la ventana.
        if lectura["dominio"] == "residuos":
            if lectura["valor"] >= UMBRAL_LLENADO and lectura["sensor"] not in self._alertados:
                self._alertados.add(lectura["sensor"])
                self._despachar({"tipo": "alerta", **lectura})
            elif lectura["valor"] < UMBRAL_LLENADO:
                self._alertados.discard(lectura["sensor"])
        cola = self._pendientes[lectura["sensor"]]
        cola.append(lectura)
        if len(cola) >= self.ventana:    # agregación por ventana
            promedio = sum(l["valor"] for l in cola) / len(cola)
            self._despachar({"tipo": "agregado", "sensor": lectura["sensor"],
                             "dominio": lectura["dominio"], "zona": self.zona,
                             "valor": round(promedio, 3), "muestras": len(cola),
                             "ts": cola[-1]["ts"]})
            cola.clear()

    def _despachar(self, mensaje):
        if self.enlace_activo:
            self._enviar(mensaje)
            self.enviadas += 1
        else:
            self._bufer.append(mensaje)  # búfer sin conexión

    def reconectar(self):
        """Vuelve el enlace y se envía lo que quedó guardado."""
        self.enlace_activo = True
        pendientes, self._bufer = self._bufer, []
        for mensaje in pendientes:
            self._enviar(mensaje)
            self.enviadas += 1
        return len(pendientes)

    @property
    def en_bufer(self):
        return len(self._bufer)
