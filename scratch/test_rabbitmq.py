import asyncio
import sys
import os

# Agrega la carpeta /backend al PATH de búsqueda de Python para poder importar 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.platform.config import settings
from app.platform.messaging.rabbitmq_event_bus import RabbitMQEventBus


async def test_rabbitmq_publish():
    print("--- INICIANDO PRUEBA DE PUBLICACIÓN DE EVENTOS EN RABBITMQ ---")
    print(f"URL de conexión: {settings.RABBITMQ_URL}")

    # Instanciar el event bus asíncrono
    event_bus = RabbitMQEventBus(settings.RABBITMQ_URL)

    try:
        # Conectar al broker
        await event_bus.connect()

        # Payload de prueba para tenant.created
        test_payload = {
            "tenantId": "c9a6a6f6-4f40-424a-8ee0-0b61869e8b7c",
            "ownerName": "Juan Perez",
            "ownerEmail": "juan@dentalx.com",
            "ownerPasswordHash": "$2b$12$EjemploDeHashBcryptParaPruebasRabbitMQ123456"
        }

        # Publicar el evento
        print("\n[Prueba] Publicando evento 'tenant.created'...")
        await event_bus.publish("tenant.created", test_payload)
        print("-> ÉXITO: Mensaje publicado en el exchange 'jchat.events'.")

        # Desconectar
        await event_bus.disconnect()
        print("\n--- PRUEBA COMPLETADA CON ÉXITO ---")

    except Exception as e:
        print(f"\n[ERROR] Falló la prueba de RabbitMQ: {e}")
        print("\n[INFO] Asegúrate de que RabbitMQ esté iniciado localmente en tu sistema.")
        print("Puedes iniciarlo con Docker ejecutando:")
        print("docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management")


if __name__ == "__main__":
    asyncio.run(test_rabbitmq_publish())
