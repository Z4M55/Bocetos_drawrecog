# ============================
# Config MQTT
# ============================
BROKER = "157.230.214.127"
PORT = 1883
MQTT_CLIENT_ID = "STREAMLIT_MYSTIC_PUB"

def mqtt_publish(topic: str, payload: dict, qos: int = 0, retain: bool = False):
    """
    Publica un mensaje MQTT usando paho-mqtt 1.6.1
    Maneja correctamente la creación del cliente con client_id obligatorio.
    """
    try:
        # Cliente compatible con la versión 1.6.1
        client = paho.Client(
            client_id=MQTT_CLIENT_ID,
            clean_session=True,
            userdata=None,
            protocol=paho.MQTTv311
        )

        # Solo mostramos publicación exitosa en consola
        def on_publish(client, userdata, mid):
            print("Publicado:", topic, payload)

        client.on_publish = on_publish

        # Conexión
        client.connect(BROKER, PORT, keepalive=60)

        # Publicación
        payload_str = json.dumps(payload)
        client.publish(topic, payload_str, qos=qos, retain=retain)

        # Cierre
        client.disconnect()
        return True, None

    except Exception as e:
        return False, str(e)
