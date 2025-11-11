import os
import streamlit as st
import base64
from openai import OpenAI
import openai
from PIL import Image
import numpy as np
from streamlit_drawable_canvas import st_canvas
import paho.mqtt.client as paho
import json
import random
import io
import tempfile
import time

# ============================
# MQTT CONFIGURACIÓN
# ============================
broker = "broker.mqttdashboard.com"
port = 1883

def on_publish(client, userdata, result):
    print("Dato publicado correctamente.")

def on_message(client, userdata, message):
    global message_received
    time.sleep(2)
    message_received = str(message.payload.decode("utf-8"))
    st.write(message_received)

client1 = paho.Client("z4m")
client1.on_publish = on_publish
client1.on_message = on_message

# ============================
# OPCIONALES: TTS
# ============================
try:
    from gtts import gTTS
    _HAS_GTTS = True
except Exception:
    _HAS_GTTS = False

try:
    import pyttsx3
    _HAS_PYTTSX3 = True
except Exception:
    _HAS_PYTTSX3 = False

# ============================
# VARIABLES DE SESIÓN
# ============================
if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False
if 'full_response' not in st.session_state:
    st.session_state.full_response = ""
if 'base64_image' not in st.session_state:
    st.session_state.base64_image = ""
if 'last_probability' not in st.session_state:
    st.session_state.last_probability = None
if 'last_angle' not in st.session_state:
    st.session_state.last_angle = None
if 'tts_audio_bytes' not in st.session_state:
    st.session_state.tts_audio_bytes = None

# ============================
# FUNCIÓN: IMAGEN A BASE64
# ============================
def encode_image_to_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except FileNotFoundError:
        return None

# ============================
# INTERFAZ PRINCIPAL
# ============================
st.set_page_config(page_title='꩜ Tablero Místico ꩜', layout="wide")
st.title('꩜ Tablero Místico de Predicciones ꩜')

st.markdown("""
Bienvenido/a al **Oráculo Digital**  
✶✶✶ Lo que traces aquí no será un simple dibujo...  
Cada línea revelará algo oculto en tu mente, y con ello... tu destino.  
Dibuja sin pensar, y cuando estés listo, pide al tablero que revele lo que el futuro guarda para ti.
✩₊˚.⋆☾𓃦☽⋆⁺₊✧
""")

# ============================
# PANEL LATERAL
# ============================
with st.sidebar:
    st.subheader("Herramientas de tu destino")
    stroke_width = st.slider('Grosor de la pluma', 1, 30, 5)
    stroke_color = st.color_picker("Color de tu energía", "#000000")
    bg_color = st.color_picker("Color de tu universo", "#FFFFFF")

# ============================
# CANVAS
# ============================
canvas_result = st_canvas(
    fill_color="rgba(255,165,0,0.3)",
    stroke_width=stroke_width,
    stroke_color=stroke_color,
    background_color=bg_color,
    height=350,
    width=450,
    drawing_mode="freedraw",
    key="canvas",
)

# ============================
# API KEY
# ============================
ke = st.text_input('🔑 Ingresa tu Clave Mágica (API Key)', type="password")
os.environ['OPENAI_API_KEY'] = ke
api_key = os.getenv('OPENAI_API_KEY', '')
client = None
if api_key:
    try:
        client = OpenAI(api_key=api_key)
    except Exception:
        client = None

# ============================
# BOTÓN: ANALIZAR DIBUJO
# ============================
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
            "Habla en tono enigmático y espiritual, con metáforas y símbolos misteriosos."
        )

        try:
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_text},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}},
                        ],
                    }
                ],
                max_tokens=500,
            )
            if response.choices[0].message.content:
                st.session_state.full_response = response.choices[0].message.content
                st.session_state.analysis_done = True
        except Exception as e:
            st.error(f"Error en la lectura del destino: {e}")

# ============================
# RESULTADO Y OPCIONES
# ============================
if st.session_state.analysis_done:
    st.divider()
    st.subheader("𓁻 Tu destino revelado 𓁻")
    st.markdown(st.session_state.full_response)

    st.divider()
    st.subheader("⋆.˚ Consejo del destino ⋆.˚")

    try:
        consejo_prompt = (
            f"Basado en esta predicción: '{st.session_state.full_response}', "
            "genera un consejo espiritual y enigmático, breve e inspirador."
        )
        consejo = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": consejo_prompt}],
            max_tokens=200,
        )
        st.markdown(consejo.choices[0].message.content)
    except Exception as e:
        st.warning(f"No se pudo obtener consejo: {e}")

    st.divider()
    st.subheader("✨ Interacciones adicionales ✨")

    col1, col2 = st.columns(2)

    # Probabilidad
    with col1:
        if st.button('Calcular probabilidad'):
            choice = random.choice(["Bajo", "Medio", "Alto"])
            angle_map = {"Bajo": 30, "Medio": 90, "Alto": 150}
            angle = angle_map[choice]
            st.session_state.last_probability = choice
            st.session_state.last_angle = angle
            st.success(f"Probabilidad: **{choice}** ({angle}°)")
            
            # Enviar MQTT
            try:
                client1.connect(broker, port)
                message = json.dumps({"Act1": choice})
                client1.publish("cmqtt_z4m", message)
            except Exception as e:
                st.error(f"No se pudo enviar MQTT: {e}")

    # TTS
    with col2:
        if st.button("Escuchar oráculo"):
            text = st.session_state.full_response
            if not text:
                st.warning("No hay texto para convertir en audio.")
            else:
                audio_bytes = None
                if _HAS_GTTS:
                    try:
                        tts = gTTS(text, lang="es")
                        bio = io.BytesIO()
                        tts.write_to_fp(bio)
                        bio.seek(0)
                        audio_bytes = bio.read()
                        st.audio(audio_bytes, format="audio/mp3")
                    except Exception as e:
                        st.error(f"Error gTTS: {e}")
                elif _HAS_PYTTSX3:
                    try:
                        engine = pyttsx3.init()
                        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                        engine.save_to_file(text, tmp.name)
                        engine.runAndWait()
                        with open(tmp.name, "rb") as f:
                            st.audio(f.read(), format="audio/wav")
                    except Exception as e:
                        st.error(f"Error pyttsx3: {e}")
                else:
                    st.error("No hay motor TTS disponible.")

if not api_key:
    st.warning("Por favor, ingresa tu Clave Mágica para invocar al Oráculo.")
