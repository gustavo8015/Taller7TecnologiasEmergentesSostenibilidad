"""Capas de servicios y almacenamiento: cola de eventos, microservicios y base de datos."""
import queue
import sqlite3
import threading
from collections import defaultdict, deque


class ColaEventos:
    """Publicación y suscripción por tema. Sustituye al intermediario de mensajes."""
    def __init__(self):
        self._suscriptores = defaultdict(list)

    def suscribir(self, tema, funcion):
        self._suscriptores[tema].append(funcion)

    def publicar(self, tema, evento):
        for funcion in self._suscriptores[tema]:
            funcion(evento)


class Almacen:
    """Base de datos SQLite compartida entre hilos mediante un candado."""
    def __init__(self, ruta=":memory:"):
        self._db = sqlite3.connect(ruta, check_same_thread=False)
        self._candado = threading.Lock()
        self.ejecutar("""CREATE TABLE IF NOT EXISTS mediciones(
            id INTEGER PRIMARY KEY, dominio TEXT, zona TEXT, sensor TEXT, valor REAL, muestras INTEGER, ts REAL)""")
        self.ejecutar("""CREATE TABLE IF NOT EXISTS alertas(
            id INTEGER PRIMARY KEY, sensor TEXT, zona TEXT, mensaje TEXT, ts REAL)""")
        self.ejecutar("""CREATE TABLE IF NOT EXISTS pronosticos(
            sensor TEXT PRIMARY KEY, dominio TEXT, valor REAL, detalle TEXT)""")

    def ejecutar(self, sql, parametros=()):
        with self._candado:
            cursor = self._db.execute(sql, parametros)
            filas = cursor.fetchall()
            self._db.commit()
            return filas


class ServicioDominio:
    """Microservicio de energía, movilidad o residuos: guarda las mediciones de su dominio."""
    def __init__(self, dominio, cola, almacen):
        self.dominio = dominio
        self._cola = cola
        self._almacen = almacen
        cola.suscribir(f"lecturas.{dominio}", self.procesar)

    def procesar(self, evento):
        if evento["tipo"] == "alerta":
            self._cola.publicar("alertas", evento)
            return
        self._almacen.ejecutar(
            "INSERT INTO mediciones(dominio, zona, sensor, valor, muestras, ts) VALUES(?,?,?,?,?,?)",
            (evento["dominio"], evento["zona"], evento["sensor"], evento["valor"], evento["muestras"], evento["ts"]))
        self._cola.publicar("mediciones.guardadas", evento)


class ServicioAnalitica:
    """Pronóstico sencillo: media móvil, y lecturas restantes para llenar un contenedor."""
    def __init__(self, cola, almacen, historial=4):
        self._almacen = almacen
        self._series = defaultdict(lambda: deque(maxlen=historial))
        cola.suscribir("mediciones.guardadas", self.procesar)

    def procesar(self, evento):
        serie = self._series[evento["sensor"]]
        serie.append(evento["valor"])
        pronostico, detalle = self.pronosticar(list(serie), evento["dominio"])
        self._almacen.ejecutar("INSERT OR REPLACE INTO pronosticos VALUES(?,?,?,?)",
                               (evento["sensor"], evento["dominio"], pronostico, detalle))

    @staticmethod
    def pronosticar(valores, dominio):
        media = round(sum(valores) / len(valores), 3)
        if dominio != "residuos" or len(valores) < 2:
            return media, "media móvil"
        pendiente = (valores[-1] - valores[0]) / (len(valores) - 1)
        if pendiente <= 0:
            return media, "sin tendencia de llenado"
        ventanas = max(0.0, (100.0 - valores[-1]) / pendiente)
        return round(valores[-1] + pendiente, 1), f"se llena en unas {ventanas:.0f} ventanas"


class ServicioNotificaciones:
    def __init__(self, cola, almacen, avisar=print):
        self._almacen = almacen
        self._avisar = avisar
        cola.suscribir("alertas", self.procesar)

    def procesar(self, evento):
        nivel = str(evento["valor"]).replace(".", ",")
        mensaje = f"Contenedor {evento['sensor']} al {nivel} %: programar recolección"
        self._almacen.ejecutar("INSERT INTO alertas(sensor, zona, mensaje, ts) VALUES(?,?,?,?)",
                               (evento["sensor"], evento["zona"], mensaje, evento["ts"]))
        self._almacen.ejecutar("DELETE FROM alertas WHERE id <= (SELECT MAX(id) FROM alertas) - 200")
        self._avisar(f"[ALERTA] {evento['zona']}: {mensaje}")


class Ingesta:
    """Recibe los mensajes de las pasarelas en un hilo propio y los publica en la cola."""
    def __init__(self, cola):
        self._cola = cola
        self._entrada = queue.Queue()
        self.recibidos = 0
        self._hilo = threading.Thread(target=self._bucle, daemon=True)
        self._hilo.start()

    def recibir(self, mensaje):          # lo llaman las pasarelas
        self._entrada.put(mensaje)

    def _bucle(self):
        while True:
            mensaje = self._entrada.get()
            if mensaje is None:
                break
            self.recibidos += 1
            self._cola.publicar(f"lecturas.{mensaje['dominio']}", mensaje)

    def cerrar(self):
        self._entrada.put(None)
        self._hilo.join()


def construir_nube(ruta_db=":memory:", avisar=print):
    cola, almacen = ColaEventos(), Almacen(ruta_db)
    for dominio in ("energia", "movilidad", "residuos"):
        ServicioDominio(dominio, cola, almacen)
    ServicioAnalitica(cola, almacen)
    ServicioNotificaciones(cola, almacen, avisar)
    return Ingesta(cola), almacen
