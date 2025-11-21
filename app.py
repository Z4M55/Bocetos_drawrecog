import os
import time
import streamlit as st
import base64
from openai import OpenAI
import openai
from PIL import Image
import numpy as np
from gtts import gTTS
from streamlit_drawable_canvas import st_canvas
import json
import paho.mqtt.client as paho

# ============================
# Fondo de la app
# ============================
def set_background(image_file: str):
   
    with open(image_file, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}
       </style>
        """,
      unsafe_allow_html=True
    )

# ============================
# Config MQTT (actualizado paho-mqtt 1.6.1)
# ============================
BROKER = "157.230.214.127"
PORT = 1883
MQTT_CLIENT_ID = "STREAMLIT_MYSTIC_PUB"

def mqtt_publish(topic: str, payload: dict, qos: int = 0, retain: bool = False):
    """
    Publica un mensaje MQTT usando paho-mqtt 1.6.1.
    Maneja correctamente la creación del cliente con client_id obligatorio.
    """
    try:
        client = paho.Client(
            client_id=MQTT_CLIENT_ID,
            clean_session=True,
            userdata=None,
            protocol=paho.MQTTv311
        )

        def on_publish(client, userdata, mid):
            print("Publicado:", topic, payload)

        client.on_publish = on_publish

        client.connect(BROKER, PORT, keepalive=60)

        payload_str = json.dumps(payload)
        client.publish(topic, payload_str, qos=qos, retain=retain)

        client.disconnect()
        return True, None
    except Exception as e:
        return False, str(e)

# ============================
# Session state
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
if 'last_mqtt_publish' not in st.session_state:
    st.session_state.last_mqtt_publish = ""
if 'slider_value' not in st.session_state:
    st.session_state.slider_value = 0.0

# ============================
# Función para convertir imagen a Base64
# ============================
def encode_image_to_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
            return encoded_image
    except FileNotFoundError:
        return "Error: La imagen no se encontró en la ruta especificada."

# ============================
# Interfaz principal
# ============================
st.set_page_config(page_title='Tablero Místico', layout="wide")

# Fondo del bosque mágico
set_background("fondo_bosque.png")

st.title(' ꩜ Tablero Místico de Predicciones ꩜ ')

st.markdown("""
Bienvenido/a al Oráculo Digital  
✶✶✶ Lo que traces aquí no será un simple dibujo...  
Cada línea, cada trazo y cada forma revelará algo oculto en tu mente, y con ello... tu destino.  
""")

# Sidebar
with st.sidebar:
    st.subheader("Herramientas de tu destino")
    stroke_width = st.slider('Grosor de la pluma', 1, 30, 5)
    stroke_color = st.color_picker("Color de tu energía", "#000000")
    bg_color = st.color_picker("Color de tu universo", "#FFFFFF")

# ============================
# Canvas grande y blanco
# ============================
canvas_width = 900
canvas_height = 450

canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",
    stroke_width=stroke_width,
    stroke_color=stroke_color,
    background_color=bg_color,
    height=canvas_height,
    width=canvas_width,
    drawing_mode="freedraw",
    key="canvas",
)

# API Key
ke = st.text_input('Ingresa tu Clave Mágica (API Key)', type="password")
os.environ['OPENAI_API_KEY'] = ke
api_key = os.environ.get('OPENAI_API_KEY', '')
client = None
if api_key:
    try:
        client = OpenAI(api_key=api_key)
    except Exception:
        client = None

# Botón para análisis
analyze_button = st.button("🔮 Revela mi futuro")

if canvas_result.image_data is not None and api_key and analyze_button:
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
            full_response = ""
            message_placeholder = st.empty()

            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_text},
                            {"type": "image_url",
                             "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                        ]
                    }
                ],
                max_tokens=500,
            )

            try:
                content = response.choices[0].message.content
            except Exception:
                content = str(response)

            if content:
                full_response += content
                message_placeholder.markdown(full_response)

            st.session_state.full_response = full_response
            st.session_state.analysis_done = True

        except Exception as e:
            st.error(f"Ocurrió un error en la lectura de tu destino: {e}")

# ============================================================
# MOSTRAR RESULTADO DEL ORÁCULO
# ============================================================
if st.session_state.analysis_done:
    st.divider()
    st.subheader("𓁻 Tu destino revelado 𓁻")
    st.markdown(st.session_state.full_response)

    st.divider()
    st.subheader("¿Quieres saber qué tan probable es este futuro?")
   st.text("Ve a la página - Probabilidad")

   advice_button = st.button("Escuchar el consejo del destino")

    # CONSEJO DEL DESTINO
    if advice_button:
        with st.spinner("Consultando un consejo del destino..."):

            consejo_prompt = (
                f"Basado en esta predicción del futuro: '{st.session_state.full_response}', "
                "genera un consejo espiritual y enigmático. Corto, profundo y místico."
            )

            try:
                consejo_response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": consejo_prompt}],
                    max_tokens=150,
                )

                try:
                    consejo_texto = consejo_response.choices[0].message.content.strip()
                except Exception:
                    consejo_texto = str(consejo_response)

            except Exception as e:
                consejo_texto = f"No se pudo obtener un consejo del destino: {e}"

        st.divider()
        st.subheader("⋆.˚Consejo del destino⋆.˚")
        st.markdown(consejo_texto)

        # TTS
        try:
            tts = gTTS(consejo_texto, lang="es")
            audio_path = "consejo_oraculo.mp3"
            tts.save(audio_path)
            audio_file = open(audio_path, "rb")
            st.audio(audio_file.read(), format="audio/mp3")
        except Exception as e:
            st.error(f"No se pudo generar el audio: {e}")

    # PROBABILIDAD DEL FUTURO
    #if want_prob:
    #    if not api_key:
    #        st.error("Necesitas ingresar tu Clave Mágica (API Key).")
    #    else:
    #        with st.spinner("El Oráculo está evaluando la probabilidad..."):

   #           prob_prompt = (
   #                 "Evalúa esta predicción y devuelve JSON:\n"
   #                 f"{st.session_state.full_response}\n\n"
   #                 "{\"label\":\"ALTO|MEDIO|BAJO\",\"confidence\":0-100,\"reason\":\"breve\"}"
   #             )

   #             try:
   #                 prob_resp = openai.chat.completions.create(
   #                     model="gpt-4o-mini",
   #                     messages=[{"role": "user", "content": prob_prompt}],
   #                     max_tokens=150,
   #                 )

   #                prob_text = prob_resp.choices[0].message.content.strip()
   #                try:
   #                    prob_json = json.loads(prob_text)
   #                 except:
   #                     prob_json = {"label": "MEDIO", "confidence": 50, "reason": "Auto-generado."}
   #                 label = prob_json.get("label", "MEDIO").upper()
   #                 conf = int(float(prob_json.get("confidence", 50)))
   #                 conf = max(0, min(100, conf))

   #                 angle_map = {"ALTO": 160, "MEDIO": 90, "BAJO": 20}
   #                 servo_angle = angle_map.get(label, 90)

   #                 st.session_state.probability_result = {
   #                     "label": label,
   #                     "confidence": conf,
   #                     "reason": prob_json.get("reason", "")
                    }
   #                 st.session_state.servo_angle = servo_angle

   #                 st.success(f"Probabilidad: **{label}** — Confianza: **{conf}%**")
   #                 st.markdown(f"**Motivo:** {prob_json.get('reason', '')}")
   #                 st.markdown(f"Ángulo sugerido: **{servo_angle}°**")

   #             except Exception as e:
   #                 st.error(f"No se pudo evaluar la probabilidad: {e}")

    # ===============================
    # BLOQUE DE ARDUINO + MQTT
    # ===============================
   # if st.session_state.probability_result is not None:
   #     st.divider()
   #     st.subheader("Implementación en Servo (Arduino)")
   #     st.markdown(f"""
   #     - Etiqueta: `{st.session_state.probability_result['label']}`
   #     - Confianza: `{st.session_state.probability_result['confidence']}%`
   #     - Ángulo sugerido: `{st.session_state.servo_angle}°`
   #     """)

   #     new_val = st.slider("Selecciona el rango de valores", 0.0, 100.0,
   #                         st.session_state.slider_value, key="corrected_slider")

   #     st.session_state.slider_value = new_val
   #     st.write("Valor seleccionado:", new_val)

   #     col_send1, col_send2 = st.columns(2)
   #     with col_send1:
   #         if st.button("Enviar ON al ESP32"):
   #             ok, err = mqtt_publish("cmqtt_s", {"Act1": "ON"})
   #             st.success("ON enviado") if ok else st.error(err)

   #     with col_send2:
   #         if st.button("Enviar OFF al ESP32"):
   #             ok, err = mqtt_publish("cmqtt_s", {"Act1": "OFF"})
   #             st.success("OFF enviado") if ok else st.error(err)

   #     if st.button("Enviar ángulo sugerido al ESP32"):
   #         servo_angle_deg = st.session_state.servo_angle or 90
   #         percent = round((servo_angle_deg / 180) * 100, 2)

   #         ok, err = mqtt_publish("cmqtt_a", {"Analog": percent})
   #         if ok:
   #             st.success(f"Publicado: {percent}")
   #             st.session_state.last_mqtt_publish = f"Sugerido: {percent}"
   #         else:
   #             st.error(err)

   #     if st.button("Enviar valor manual al ESP32"):
   #         val = float(st.session_state.slider_value)
   #         ok, err = mqtt_publish("cmqtt_a", {"Analog": val})
   #         if ok:
   #             st.success(f"Enviado: {val}")
   #             st.session_state.last_mqtt_publish = f"Manual: {val}"
   #         else:
   #             st.error(err)

   #     st.markdown("**Última publicación MQTT:**")
   #     st.write(st.session_state.last_mqtt_publish)
