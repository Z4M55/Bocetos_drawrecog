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
import time

# ============================
# Intentos de importación TTS
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
# Variables MQTT
# ============================
message_received = ""

def on_publish(client, userdata, result):
    print("El dato ha sido publicado")
    pass

def on_message(client, userdata, message):
    global message_received
    time.sleep(2)
    message_received = str(message.payload.decode("utf-8"))
    st.write(message_received)

broker = "broker.mqttdashboard.com"
port = 1883

# ============================
# Inicializar session_state
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
if 'tts_audio_bytes' not in st.session_state:
    st.session_state.tts_audio_bytes = None
if 'consejo_texto' not in st.session_state:
    st.session_state.consejo_texto = ""

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
# API Key
# ============================
ke = st.text_input('Ingresa tu Clave Mágica (API Key)', type="password")
os.environ['OPENAI_API_KEY'] = ke
api_key = os.environ.get('OPENAI_API_KEY', '')

# ============================
# Botón para análisis principal
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
# Mostrar resultado y opciones de interacción
# ============================
if st.session_state.analysis_done:
    st.divider()
    st.subheader("𓁻 Tu destino revelado 𓁻")
    st.markdown(f"{st.session_state.full_response}")

    st.divider()
    st.subheader("✨ Interacciones místicas adicionales")

    # ============================
    # INTERACCIÓN 1: Generar consejo del destino
    # ============================
    if st.button("💫 Recibir consejo del destino"):
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
                st.session_state.consejo_texto = consejo_response.choices[0].message.content.strip()
            except Exception as e:
                st.session_state.consejo_texto = f"No se pudo obtener un consejo del destino: {e}"

    # Mostrar consejo si existe
    if st.session_state.consejo_texto:
        st.divider()
        st.markdown("### ⋆.˚ Consejo del destino ⋆.˚")
        st.markdown(st.session_state.consejo_texto)

    # ============================
    # INTERACCIÓN 2: Text-to-Speech
    # ============================
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("🔊 Escuchar oráculo"):
            if not st.session_state.full_response:
                st.warning("No hay texto del oráculo para convertir en audio.")
            else:
                text_to_speak = st.session_state.full_response
                audio_bytes = None
                tts_error = None

                # Intentar con gTTS
                if _HAS_GTTS:
                    try:
                        tts = gTTS(text_to_speak, lang="es")
                        bio = io.BytesIO()
                        tts.write_to_fp(bio)
                        bio.seek(0)
                        audio_bytes = bio.read()
                        st.session_state.tts_audio_bytes = audio_bytes
                        st.success("🎵 Audio generado con gTTS.")
                    except Exception as e:
                        tts_error = f"gTTS falló: {e}"

                # Fallback a pyttsx3
                if audio_bytes is None and _HAS_PYTTSX3:
                    try:
                        import tempfile
                        engine = pyttsx3.init()
                        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                            tmp_path = f.name
                        engine.save_to_file(text_to_speak, tmp_path)
                        engine.runAndWait()
                        with open(tmp_path, "rb") as f:
                            audio_bytes = f.read()
                        try:
                            os.remove(tmp_path)
                        except Exception:
                            pass
                        st.session_state.tts_audio_bytes = audio_bytes
                        st.success("🎵 Audio generado con pyttsx3.")
                    except Exception as e:
                        if tts_error:
                            tts_error += f" | pyttsx3 falló: {e}"
                        else:
                            tts_error = f"pyttsx3 falló: {e}"

                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3" if _HAS_GTTS else "audio/wav")
                else:
                    st.error("No se pudo generar audio. Instala gTTS o pyttsx3.")
                    if tts_error:
                        st.write(tts_error)

    # ============================
    # INTERACCIÓN 3: Calcular probabilidad y enviar a Arduino via MQTT
    # ============================
    with col2:
        if st.button('⚡ Calcular probabilidad y enviar a servo'):
            with st.spinner("Evaluando probabilidad..."):
                prob_prompt = (
                    "Eres un analista místico. Lee la siguiente predicción y evalúa qué tan probable es que ese futuro "
                    "se cumpla: \n\n"
                    f"Predicción:\n{st.session_state.full_response}\n\n"
                    "Devuélvelo en formato JSON simple: "
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
                        prob_json = {"label": "MEDIO", "confidence": 50, "reason": "Estimación mística automática."}

                    label = prob_json.get("label", "MEDIO").upper()
                    confidence = prob_json.get("confidence", 50)
                    reason = prob_json.get("reason", "")

                    # Mapear a ángulos para servo
                    angle_map = {"ALTO": 160, "ALTA": 160, "MEDIO": 90, "BAJO": 20, "BAJA": 20}
                    servo_angle = angle_map.get(label, 90)

                    st.session_state.probability_result = {
                        "label": label, 
                        "confidence": confidence, 
                        "reason": reason
                    }
                    st.session_state.servo_angle = servo_angle

                    # Enviar vía MQTT
                    try:
                        client1 = paho.Client("z4m_mystic")
                        client1.on_publish = on_publish
                        client1.connect(broker, port)
                        message = json.dumps({
                            "probability": label,
                            "angle": servo_angle,
                            "confidence": confidence
                        })
                        ret = client1.publish("cmqtt_z4m", message)
                        st.success(f"✅ Mensaje MQTT enviado: {label} → {servo_angle}°")
                    except Exception as mqtt_error:
                        st.warning(f"⚠️ No se pudo conectar a MQTT: {mqtt_error}")

                    st.success(f"🎯 Probabilidad: **{label}** — Confianza: **{confidence}%**")
                    st.markdown(f"**Motivo:** {reason}")
                    st.markdown(f"**Ángulo servo:** **{servo_angle}°**")
                    
                except Exception as e:
                    st.error(f"No se pudo evaluar la probabilidad: {e}")

    # ============================
    # Mostrar resultado de probabilidad persistente
    # ============================
    if st.session_state.probability_result is not None:
        st.divider()
        st.subheader("🎛️ Configuración del Servo (Arduino)")
        st.markdown(f"""
        **Resumen de la última evaluación**
        - Etiqueta: `{st.session_state.probability_result.get("label")}`  
        - Confianza: `{st.session_state.probability_result.get("confidence")}%`  
        - Ángulo sugerido: `{st.session_state.servo_angle}°`  
        
        **Conexión del servo:**
        1. Señal (amarillo/naranja) → Pin PWM (ej. D9)  
        2. VCC (rojo) → 5V  
        3. GND (negro/marrón) → GND  
        
        **Código Arduino ejemplo:**
        ```cpp
        #include <Servo.h>
        Servo myservo;
        
        void setup() {{
          myservo.attach(9);
          Serial.begin(9600);
        }}
        
        void loop() {{
          if (Serial.available() > 0) {{
            int angle = Serial.parseInt();
            myservo.write(angle);
          }}
        }}
        ```
        """)

if not api_key:
    st.warning("⚠️ Por favor, ingresa tu Clave Mágica para invocar al Oráculo.")
