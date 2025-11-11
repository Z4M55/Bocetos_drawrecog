import os
import streamlit as st
import base64
from openai import OpenAI
import openai
from PIL import Image
import numpy as np
from gtts import gTTS
from streamlit_drawable_canvas import st_canvas
import json
import random
import time
import platform
import paho.mqtt.client as paho
import io
import tempfile

# ============================
# Configuración MQTT por defecto (puedes editar desde la UI)
# ============================
DEFAULT_MQTT_BROKER = "157.230.214.127"
DEFAULT_MQTT_PORT = 1883
DEFAULT_MQTT_TOPIC = "cmqtt_s"

# ============================
# Variables / session_state
# ============================
if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False
if 'full_response' not in st.session_state:
    st.session_state.full_response = ""
if 'base64_image' not in st.session_state:
    st.session_state.base64_image = ""
if 'probability_result' not in st.session_state:
    st.session_state.probability_result = None
if 'servo_angle' not in st.session_state:
    st.session_state.servo_angle = None
if 'consejo_texto' not in st.session_state:
    st.session_state.consejo_texto = ""

# ============================
# Utilidades
# ============================
def encode_image_to_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except FileNotFoundError:
        return None

def publish_mqtt_message(broker: str, port: int, topic: str, payload: dict):
    """
    Publica payload (dict) como JSON en el topic MQTT.
    Retorna (ok: bool, error_msg: str|None)
    """
    try:
        client = paho.Client("oraculo_streamlit_" + str(random.randint(0,9999)))
        client.connect(broker, port, keepalive=60)
        client.loop_start()
        payload_str = json.dumps(payload)
        client.publish(topic, payload_str)
        time.sleep(0.1)
        client.loop_stop()
        client.disconnect()
        return True, None
    except Exception as e:
        return False, str(e)

def text_to_speech_and_play(text: str, filename_hint: str = "tts_output"):
    """
    Genera audio mp3 con gTTS y lo devuelve como bytes para st.audio.
    """
    try:
        tts = gTTS(text, lang="es")
        bio = io.BytesIO()
        tts.write_to_fp(bio)
        bio.seek(0)
        return bio.read(), None
    except Exception as e:
        return None, str(e)

# ============================
# Interfaz principal
# ============================
st.set_page_config(page_title='Tablero Místico', layout="wide")
st.title(' ꩜ Tablero Místico de Predicciones ꩜ ')
st.write("Versión de Python:", platform.python_version())

st.markdown("""
Bienvenido/a al Oráculo Digital  
✶✶✶ Dibuja sin pensar y cuando estés listo, pide al tablero que revele lo que el futuro guarda para ti.  
✩₊˚.⋆☾𓃦☽⋆⁺₊✧
""")

# ============================
# Panel lateral (herramientas)
# ============================
with st.sidebar:
    st.subheader("Herramientas de tu destino")
    stroke_width = st.slider('Grosor de la pluma', 1, 30, 5)
    stroke_color = st.color_picker("Color de tu energía", "#000000")
    bg_color = st.color_picker("Color de tu universo", "#FFFFFF")
    st.divider()
    st.subheader("MQTT (ajustes)")
    mqtt_broker = st.text_input("Broker MQTT", value=DEFAULT_MQTT_BROKER)
    mqtt_port = st.number_input("Puerto MQTT", value=DEFAULT_MQTT_PORT, min_value=1, max_value=65535)
    mqtt_topic = st.text_input("Topic MQTT", value=DEFAULT_MQTT_TOPIC)

# ============================
# Canvas para dibujar
# ============================
canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",
    stroke_width=stroke_width,
    stroke_color=stroke_color,
    background_color=bg_color,
    height=350,
    width=450,
    drawing_mode="freedraw",
    key="canvas",
)

# ============================
# API Key OpenAI
# ============================
ke = st.text_input('Ingresa tu Clave Mágica (API Key)', type="password")
os.environ['OPENAI_API_KEY'] = ke
api_key = os.environ.get('OPENAI_API_KEY', '')
client = None
if api_key:
    try:
        client = OpenAI(api_key=api_key)
    except Exception:
        client = None

# ============================
# Botón Revelar (dibujo → Oráculo)
# ============================
if st.button("🔮 Revela mi futuro"):
    if canvas_result.image_data is None:
        st.warning("Dibuja algo en el tablero antes de pedir la lectura.")
    elif not api_key:
        st.warning("Ingresa tu Clave Mágica (API Key) para invocar al Oráculo.")
    else:
        with st.spinner("Consultando al Oráculo..."):
            input_numpy_array = np.array(canvas_result.image_data)
            input_image = Image.fromarray(input_numpy_array.astype('uint8')).convert('RGBA')
            input_image.save('img.png')
            base64_image = encode_image_to_base64("img.png")
            st.session_state.base64_image = base64_image

            prompt_text = (
                "Eres un oráculo místico. Basado en este dibujo, interpreta el destino del usuario. "
                "Habla en tono enigmático y espiritual, como si estuvieras revelando un secreto profundo sobre su futuro. "
                "Predice con metáforas, símbolos y un aire de misterio."
            )

            try:
                # Llamada a OpenAI (same as before)
                response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt_text},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/png;base64,{st.session_state.base64_image}"},
                                },
                            ],
                        }
                    ],
                    max_tokens=500,
                )

                full_response = ""
                if response.choices and response.choices[0].message.content:
                    full_response = response.choices[0].message.content
                else:
                    full_response = "El oráculo no pudo interpretar tu dibujo claramente."

                st.session_state.full_response = full_response
                st.session_state.analysis_done = True
                st.success("Lectura completada.")
            except Exception as e:
                st.error(f"Ocurrió un error en la lectura de tu destino: {e}")

# ============================
# Mostrar resultado y acciones (si hay lectura)
# ============================
if st.session_state.analysis_done:
    st.divider()
    st.subheader("𓁻 Tu destino revelado 𓁻")
    st.markdown(st.session_state.full_response)

    # Conseguir consejo (pero no auto-generar hasta que el usuario lo pida)
    col1, col2, col3 = st.columns([1,1,1])

    # Btn: Generar y escuchar consejo
    with col1:
        if st.button("✦ Generar consejo del destino"):
            with st.spinner("Generando consejo..."):
                consejo_prompt = (
                    f"Basado en esta predicción del futuro: '{st.session_state.full_response}', "
                    "genera un consejo espiritual y enigmático. "
                    "El consejo debe ser breve, inspirador y sonar como una guía del destino. "
                    "Usa metáforas y un tono místico."
                )
                try:
                    consejo_response = openai.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": consejo_prompt}],
                        max_tokens=200,
                    )
                    consejo_texto = consejo_response.choices[0].message.content.strip()
                except Exception as e:
                    consejo_texto = f"No se pudo obtener un consejo del destino: {e}"

                st.session_state.consejo_texto = consejo_texto
                st.success("Consejo generado.")

    # Btn: Escuchar predicción completa (TTS)
    with col2:
        if st.button("🔊 Escuchar predicción (Text-to-Speech)"):
            if not st.session_state.full_response:
                st.warning("No hay predicción para leer. Ejecuta 'Revela mi futuro' primero.")
            else:
                audio_bytes, err = text_to_speech_and_play(st.session_state.full_response)
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3")
                    st.success("Reproduciendo la predicción.")
                else:
                    st.error(f"No se pudo generar audio: {err}")

    # Btn: Escuchar consejo (TTS) — usa consejo_texto (genera si no existe)
    with col3:
        if st.button("🔔 Escuchar consejo (Text-to-Speech)"):
            # si no hay consejo aún, generarlo automáticamente
            if not st.session_state.consejo_texto:
                with st.spinner("Generando consejo..."):
                    consejo_prompt = (
                        f"Basado en esta predicción del futuro: '{st.session_state.full_response}', "
                        "genera un consejo espiritual y enigmático. "
                        "El consejo debe ser breve, inspirador y sonar como una guía del destino. "
                        "Usa metáforas y un tono místico."
                    )
                    try:
                        consejo_response = openai.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[{"role": "user", "content": consejo_prompt}],
                            max_tokens=200,
                        )
                        st.session_state.consejo_texto = consejo_response.choices[0].message.content.strip()
                    except Exception as e:
                        st.session_state.consejo_texto = f"No se pudo obtener un consejo del destino: {e}"

            if st.session_state.consejo_texto:
                audio_bytes, err = text_to_speech_and_play(st.session_state.consejo_texto)
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3")
                    st.success("Reproduciendo el consejo.")
                else:
                    st.error(f"No se pudo generar audio: {err}")

    st.divider()

    # ============================
    # PROBABILIDAD (botón) → calcula label y ángulo → publica por MQTT si se selecciona
    # ============================
    st.subheader("¿Quieres saber qué tan probable es este futuro?")
    colp1, colp2 = st.columns([2,1])
    with colp1:
        if st.button("Calcular probabilidad mística"):
            if not api_key:
                st.error("Necesitas ingresar tu Clave Mágica (API Key) para que el Oráculo calcule la probabilidad.")
            else:
                with st.spinner("El Oráculo evalúa la probabilidad..."):
                    prob_prompt = (
                        "Eres un analista místico. Lee la siguiente predicción y evalúa qué tan probable es que ese futuro "
                        "se cumpla: \n\n"
                        f"Predicción:\n{st.session_state.full_response}\n\n"
                        "Devuélvelo en formato JSON simple EXACTO: "
                        "{\"label\":\"ALTO|MEDIO|BAJO\",\"confidence\":<porcentaje entre 0 y 100>," 
                        "\"reason\":\"una frase breve explicando por qué\"}. Solo devuelve JSON."
                    )
                    try:
                        prob_resp = openai.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[{"role": "user", "content": prob_prompt}],
                            max_tokens=150,
                        )
                        prob_text = prob_resp.choices[0].message.content.strip()
                        try:
                            prob_json = json.loads(prob_text)
                        except Exception:
                            # fallback aleatorio si la respuesta no es JSON
                            prob_json = {"label": random.choice(["ALTO", "MEDIO", "BAJO"]), "confidence": random.randint(30,90), "reason": "Estimación mística automática."}
                    except Exception as e:
                        prob_json = {"label": random.choice(["ALTO", "MEDIO", "BAJO"]), "confidence": random.randint(30,90), "reason": f"Estimación automática por error: {e}"}

                    label = str(prob_json.get("label", "MEDIO")).upper()
                    confidence = prob_json.get("confidence", 50)
                    reason = prob_json.get("reason", "")

                    angle_map = {"ALTO": 150, "MEDIO": 90, "BAJO": 30}
                    servo_angle = angle_map.get(label, 90)

                    st.session_state.probability_result = {"label": label, "confidence": confidence, "reason": reason}
                    st.session_state.servo_angle = servo_angle

                    st.success(f"Probabilidad: **{label}** — Confianza: **{confidence}%**")
                    st.markdown(f"**Motivo:** {reason}")
                    st.markdown(f"**Ángulo sugerido para el servo:** **{servo_angle}°**")

    with colp2:
        publish_checkbox = st.checkbox("Publicar probabilidad por MQTT automáticamente", value=False)

    # Si se seleccionó publicar y ya hay probabilidad calculada, permitir publicar ahora
    if publish_checkbox and st.session_state.probability_result:
        if st.button("Publicar resultado por MQTT ahora"):
            payload = {
                "servo_prob": st.session_state.probability_result.get("label"),
                "confidence": st.session_state.probability_result.get("confidence"),
                "angle": st.session_state.servo_angle,
                "reason": st.session_state.probability_result.get("reason")
            }
            ok, err = publish_mqtt_message(mqtt_broker, int(mqtt_port), mqtt_topic, payload)
            if ok:
                st.success(f"Publicado en {mqtt_broker}:{mqtt_port} → topic: {mqtt_topic}")
            else:
                st.error(f"No se pudo publicar por MQTT: {err}")

    # ============================
    # Controles manuales directos del servo (Bajo/Medio/Alto) que publican por MQTT
    # ============================
    st.divider()
    st.subheader("Control manual del servo (publica por MQTT)")
    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        if st.button("Mover servo → Bajo (30°)"):
            payload = {"servo_cmd": "Bajo", "angle": 30}
            ok, err = publish_mqtt_message(mqtt_broker, int(mqtt_port), mqtt_topic, payload)
            if ok:
                st.success("Comando Bajo enviado por MQTT.")
            else:
                st.error(f"Error al publicar: {err}")
    with c2:
        if st.button("Mover servo → Medio (90°)"):
            payload = {"servo_cmd": "Medio", "angle": 90}
            ok, err = publish_mqtt_message(mqtt_broker, int(mqtt_port), mqtt_topic, payload)
            if ok:
                st.success("Comando Medio enviado por MQTT.")
            else:
                st.error(f"Error al publicar: {err}")
    with c3:
        if st.button("Mover servo → Alto (150°)"):
            payload = {"servo_cmd": "Alto", "angle": 150}
            ok, err = publish_mqtt_message(mqtt_broker, int(mqtt_port), mqtt_topic, payload)
            if ok:
                st.success("Comando Alto enviado por MQTT.")
            else:
                st.error(f"Error al publicar: {err}")

    # Mostrar resumen si existe probabilidad calculada
    if st.session_state.probability_result:
        st.divider()
        st.markdown("**Última probabilidad calculada**")
        st.write(st.session_state.probability_result)
        st.write(f"Ángulo sugerido: {st.session_state.servo_angle}°")

# Recordatorio de API key
if not api_key:
    st.warning("Por favor, ingresa tu Clave Mágica (API Key) para invocar al Oráculo.")
