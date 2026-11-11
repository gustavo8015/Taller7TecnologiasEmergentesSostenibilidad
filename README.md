# Taller 7: prototipo de la plataforma urbana integrada

Sistemas Distribuidos, Ingeniería de Software, Universidad Manuela Beltrán.

Simulación funcional de la arquitectura propuesta en el Taller 7 (tecnologías emergentes y sostenibilidad en sistemas distribuidos): sensores IoT de energía, movilidad y residuos, pasarelas de borde, servicios en la nube y un tablero web.

## Cómo ejecutarlo

Requiere Python 3.8 o superior. No hay que instalar paquetes.

```
python main.py
```

La simulación corre sin límite de tiempo y el tablero queda en http://localhost:8000. Se detiene con Ctrl+C y entonces imprime el resumen.

Opciones: `--segundos 60` para que se detenga sola, `--puerto 8080`, `--corte-cada 60` y `--corte-dura 10` para el corte de enlace.

## Qué simula

- `sensores.py`: 18 sensores de energía, movilidad y residuos en tres zonas, con lecturas erróneas ocasionales.
- `pasarela.py`: una pasarela de borde por zona. Descarta lecturas fuera de rango, envía un promedio cada cinco lecturas, avisa de inmediato cuando un contenedor supera el 80 % y guarda los mensajes en un búfer si pierde el enlace.
- `nube.py`: servicio de ingesta, cola de eventos, microservicios de energía, movilidad y residuos, analítica (media móvil y estimación de llenado), notificaciones y base de datos SQLite.
- `api.py`: puerta de enlace de API (`/api/resumen`) y tablero web con filtro por dominio.

Cada 60 segundos la pasarela de la zona Sur pierde la conexión durante 10 segundos y luego envía lo que guardó. La base conserva las últimas 5.000 mediciones y 200 alertas para que la simulación pueda correr indefinidamente.

## Pruebas

```
python -m unittest discover -s tests
```

## Alcance

Es una simulación en un solo proceso. La cola de eventos sustituye a MQTT y los microservicios son clases de Python, no contenedores en Kubernetes.
