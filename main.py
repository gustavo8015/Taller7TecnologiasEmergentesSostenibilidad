"""Simulación de la plataforma urbana integrada.

Uso:  python main.py                 (sin límite de tiempo; tablero en http://localhost:8000; Ctrl+C para detener)
      python main.py --segundos 60    (se detiene sola)
      python main.py --puerto 8080
"""
import argparse
import time

from api import iniciar_api, resumen
from nube import construir_nube
from pasarela import Pasarela
from sensores import Sensor

ZONAS = ["Centro", "Norte", "Sur"]


def crear_ciudad(ingesta, semilla=7):
    pasarelas, sensores = [], []
    for i, zona in enumerate(ZONAS):
        pasarela = Pasarela(zona, ingesta.recibir)
        pasarelas.append(pasarela)
        for dominio in ("energia", "movilidad", "residuos"):
            for n in (1, 2):
                sensor = Sensor(f"{dominio[:3]}-{zona[:3].lower()}-{n}", dominio, zona, semilla + i * 10 + n + len(dominio))
                sensores.append((sensor, pasarela))
    return pasarelas, sensores


def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("--segundos", type=int, default=0, help="duración; 0 = sin límite (se detiene con Ctrl+C)")
    args.add_argument("--puerto", type=int, default=8000)
    args.add_argument("--intervalo", type=float, default=0.2, help="segundos entre lecturas")
    args.add_argument("--corte-cada", type=int, default=60, help="cada cuántos segundos la pasarela Sur pierde el enlace")
    args.add_argument("--corte-dura", type=int, default=10, help="segundos que dura cada corte")
    op = args.parse_args()

    ingesta, almacen = construir_nube()
    pasarelas, sensores = crear_ciudad(ingesta)
    iniciar_api(almacen, pasarelas, op.puerto)
    duracion = f"durante {op.segundos} s" if op.segundos else "sin límite de tiempo (Ctrl+C para detener)"
    print(f"Tablero disponible en http://localhost:{op.puerto} {duracion}")

    inicio = time.time()
    sur = pasarelas[-1]
    try:
        while True:
            transcurrido = time.time() - inicio
            if op.segundos and transcurrido >= op.segundos:
                break
            # Corte periódico de enlace en la zona Sur: empieza a mitad de cada ciclo.
            en_corte = (transcurrido % op.corte_cada) >= op.corte_cada / 2 and \
                       (transcurrido % op.corte_cada) < op.corte_cada / 2 + op.corte_dura
            if en_corte and sur.enlace_activo:
                sur.enlace_activo = False
                print("[ENLACE] La pasarela Sur perdió la conexión; guarda sus mensajes en el búfer")
            elif not en_corte and not sur.enlace_activo:
                print(f"[ENLACE] La pasarela Sur recuperó la conexión y envió {sur.reconectar()} mensajes guardados")
            for sensor, pasarela in sensores:
                lectura = sensor.leer()
                pasarela.recibir(lectura)
                if sensor.dominio == "residuos" and lectura["valor"] >= 100:
                    sensor.vaciar()                     # el camión recoge el contenedor lleno
            almacen.ejecutar(                           # retención: solo las últimas 5.000 mediciones
                "DELETE FROM mediciones WHERE id <= (SELECT MAX(id) FROM mediciones) - 5000")
            time.sleep(op.intervalo)
    except KeyboardInterrupt:
        print("\nSimulación detenida por el usuario")

    if not sur.enlace_activo:
        sur.reconectar()
    ingesta.cerrar()
    datos = resumen(almacen, pasarelas)
    borde = datos["borde"]
    print("\nResumen")
    print(f"  Lecturas recibidas en el borde: {borde['recibidas']} (descartadas por inválidas: {borde['descartadas']})")
    print(f"  Mensajes enviados a la nube:    {borde['enviadas']}")
    print(f"  Tráfico evitado por el filtrado en el borde: {borde['reduccion']} %")
    print(f"  Alertas de recolección: {almacen.ejecutar('SELECT COUNT(*) FROM alertas')[0][0]}")
    for dominio, zona, promedio, registros, _ in datos["promedios"]:
        print(f"  {dominio:<10}{zona:<8}promedio {promedio:<8}({registros} registros)")


if __name__ == "__main__":
    main()
