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
import platform
# Nuevas importaciones
import random
import io
import tempfile
import time


values = 0.0
act1="OFF"

def on_publish(client,userdata,result):             #create function for callback
    print("el dato ha sido publicado \n")
    pass

def on_message(client, userdata, message):
    global message_received
    time.sleep(2)
    message_received=str(message.payload.decode("utf-8"))
    st.write(message_received)

    
# Intentos para TTS/Serial (no son obligatorios, el código funciona aunque no estén instalados)

values = 0.0
act1="OFF"

def on_publish(client,userdata,result):             #create function for callback
    print("el dato ha sido publicado \n")
    pass

def on_message(client, userdata, message):
    global message_received
    time.sleep(2)
    message_received=str(message.payload.decode("utf-8"))
    st.write(message_received)

        


broker="broker.mqttdashboard.com"
port=1883
client1= paho.Client("z4m")
client1.on_message = on_message

if st.button('Calcular probabilidad',key='2'):
   
    choice = random.choice(["Bajo", "Medio", "Alto"])
        # Mapear a ángulos para servo

    client1= paho.Client("z4m")                           
    client1.on_publish = on_publish                          
    client1.connect(broker,port)  
    message =json.dumps({"Act1":choice})
    ret= client1.publish("cmqtt_z4m", message)
 
    #client1.subscribe("Sensores")
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

try:
    import serial
    _HAS_PYSERIAL = True
except Exception:
    _HAS_PYSERIAL = False

# ============================
# Variables
# ============================
Expert = " "
profile_imgenh = " "

# ============================
# Inicializar session_state
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
st.title(' ꩜ Tablero Místico de Predicciones ꩜ ')

st.markdown("""
Bienvenido/a al Oráculo Digital
✶✶✶ Lo que traces aquí no será un simple dibujo...  
Cada línea, cada trazo y cada forma revelará algo oculto en tu mente, y con ello... tu destino.  

Dibuja sin pensar y cuando estés listo, pide al tablero que revele lo que el futuro guarda para ti.
✩₊˚.⋆☾𓃦☽⋆⁺₊✧
""")

# ============================
# Panel lateral
# ============================
with st.sidebar:
    st.subheader("Herramientas de tu destino")
    stroke_width = st.slider('Grosor de la pluma', 1, 30, 5)
    stroke_color = st.color_picker("Color de tu energía", "#000000")
    bg_color = st.color_picker("Color de tu universo", "#FFFFFF")

# ============================
# Canvas para dibujar
# ============================
drawing_mode = "freedraw"
canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.3)",
    stroke_width=stroke_width,
    stroke_color=stroke_color,
    background_color=bg_color,
    height=350,
    width=450,
    drawing_mode=drawing_mode,
    key="canvas",
)

# ============================
# API Key
# ============================
ke = st.text_input('Ingresa tu Clave Mágica (API Key)', type="password")
os.environ['OPENAI_API_KEY'] = ke
api_key = os.environ['OPENAI_API_KEY']
client = OpenAI(api_key=api_key)

# ============================
# Botón para análisis
# ============================
analyze_button = st.button("Revela mi futuro")

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
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                            },
                        ],
                    }
                ],
                max_tokens=500,
            )

            if response.choices[0].message.content is not None:
                full_response += response.choices[0].message.content
                message_placeholder.markdown(full_response)

            st.session_state.full_response = full_response
            st.session_state.analysis_done = True

        except Exception as e:
            st.error(f"Ocurrió un error en la lectura de tu destino: {e}")

# ============================
# Mostrar resultado y nuevas interacciones
# ============================
if st.session_state.analysis_done:
    st.divider()
    st.subheader("𓁻 Tu destino revelado 𓁻")
    st.markdown(f"{st.session_state.full_response}")

    # Generar consejo del destino
    with st.spinner("Consultando un consejo del destino..."):
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
            consejo_texto = consejo_response.choices[0].message.content
        except Exception as e:
            consejo_texto = f"No se pudo obtener un consejo del destino: {e}"

    st.divider()
    st.subheader("⋆.˚Consejo del destino⋆.˚")
    st.markdown(consejo_texto)

    st.divider()
    st.subheader("Interacciones adicionales")

    # --------------------
    # Botón 1: Probabilidad (alto/medio/bajo) -> random -> opcional enviar a Arduino
    # --------------------
    st.markdown("**¿Quieres saber qué tan probable es este futuro?**")
    col1, col2 = st.columns([1, 1])

    with col1:
        prob_button = st.button("Calcular probabilidad")
        

    # Opciones para Arduino / Serial (solo visibles si el usuario quiere enviar)
    with st.expander("Opciones de implementación en servo (Arduino) — opcional"):
        st.markdown("Si deseas, puedes enviar el resultado al Arduino/servo. Se enviará el ángulo (ej. 30, 90, 150).")
        serial_port = st.text_input("Puerto serie (ej. COM3 o /dev/ttyUSB0)", value="")
        baudrate = st.number_input("Baudrate", min_value=300, max_value=115200, value=9600, step=1)
        enviar_serial = st.checkbox("Enviar resultado al Arduino/servo vía Serial (siempre que pyserial esté instalado)")

    if prob_button:
        # elección aleatoria
        choice = random.choice(["Bajo", "Medio", "Alto"])
        # Mapear a ángulos para servo
        angle_map = {"Bajo": 30, "Medio": 90, "Alto": 150}
        angle = angle_map[choice]

        st.session_state.last_probability = choice
        st.session_state.last_angle = angle

        st.success(f"Probabilidad estimada: **{choice}**")
        st.info(f"Mapa práctico para servo: {choice} → {angle}° (Izq/Centro/Der)")

        # Intentar enviar por serial si el usuario lo pidió
        if enviar_serial:
            if not _HAS_PYSERIAL:
                st.error("pyserial no está instalado en este entorno. Instálalo (pip install pyserial) para enviar datos al Arduino.")
            elif not serial_port:
                st.warning("Ingresa el puerto serie (ej. COM3 o /dev/ttyUSB0) para enviar el ángulo al Arduino.")
            else:
                try:
                    st.info("Intentando abrir puerto serie y enviar el ángulo...")
                    ser = serial.Serial(serial_port, baudrate, timeout=2)
                    time.sleep(2)  # esperar un poco a que se equilibrie la conexión
                    send_str = f"{angle}\n"
                    ser.write(send_str.encode('utf-8'))
                    ser.flush()
                    ser.close()
                    st.success(f"Ángulo {angle} enviado correctamente al puerto {serial_port}.")
                except Exception as e:
                    st.error(f"No se pudo enviar por serial: {e}")

        # Mostrar snippet/ejemplo de Arduino para implementar en el microcontrolador:
        st.markdown("**Ejemplo de código Arduino (para el servo) que puedes usar más adelante:**")
        st.code("""
#include <Servo.h>

Servo myservo;

void setup() {
  Serial.begin(9600);
  myservo.attach(9); // pin del servo
}

void loop() {
  if (Serial.available() > 0) {
    int angle = Serial.parseInt(); // lee el ángulo enviado por Streamlit (ej: 30, 90, 150)
    if (angle >= 0 && angle <= 180) {
      myservo.write(angle);
    }
    // limpiar buffer
    while (Serial.available() > 0) Serial.read();
  }
}
        """, language="cpp")

    # --------------------
    # Botón 2: Text-to-Speech para escuchar la predicción
    # --------------------
    with col2:
        tts_button = st.button("Escuchar oráculo")

    if tts_button:
        if not st.session_state.full_response:
            st.warning("No hay texto del oráculo para convertir en audio. Primero ejecuta 'Revela mi futuro'.")
        else:
            text_to_speak = st.session_state.full_response
            # Intento con gTTS primero
            audio_bytes = None
            tts_error = None

            if _HAS_GTTS:
                try:
                    tts = gTTS(text_to_speak, lang="es")
                    bio = io.BytesIO()
                    tts.write_to_fp(bio)
                    bio.seek(0)
                    audio_bytes = bio.read()
                    st.session_state.tts_audio_bytes = audio_bytes
                    st.success("Audio generado con gTTS.")
                except Exception as e:
                    tts_error = f"gTTS falló: {e}"

            # Fallback a pyttsx3 (offline)
            if audio_bytes is None and _HAS_PYTTSX3:
                try:
                    engine = pyttsx3.init()
                    # crear archivo temporal WAV
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                        tmp_path = f.name
                    engine.save_to_file(text_to_speak, tmp_path)
                    engine.runAndWait()
                    # leer bytes
                    with open(tmp_path, "rb") as f:
                        audio_bytes = f.read()
                    # remover archivo temporal
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass
                    st.session_state.tts_audio_bytes = audio_bytes
                    st.success("Audio generado con pyttsx3.")
                except Exception as e:
                    if tts_error:
                        tts_error += f" | pyttsx3 falló: {e}"
                    else:
                        tts_error = f"pyttsx3 falló: {e}"

            if audio_bytes:
                st.audio(audio_bytes, format="audio/mp3" if _HAS_GTTS else "audio/wav")
            else:
                st.error("No se pudo generar audio con gTTS ni pyttsx3 en este entorno.")
                if tts_error:
                    st.write(tts_error)

    # Mostrar último resultado de probabilidad si existe
    if st.session_state.last_probability:
        st.divider()
        st.markdown("**Última probabilidad calculada:**")
        st.write(f"Probabilidad: **{st.session_state.last_probability}** — Ángulo sugerido para servo: **{st.session_state.last_angle}°**")

if not api_key:
    st.warning("Por favor, ingresa tu Clave Mágica para invocar al Oráculo.")
