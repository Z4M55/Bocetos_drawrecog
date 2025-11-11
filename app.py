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
import random
import io
import tempfile
import time
import streamlit.components.v1 as components

# Intent imports (no fallan si no están instalados)
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
# MQTT basic callbacks (puedes extender)
# ============================
def on_publish(client, userdata, result):
    print("el dato ha sido publicado")
    pass

def on_message(client, userdata, message):
    global message_received
    time.sleep(2)
    message_received = str(message.payload.decode("utf-8"))
    st.write(message_received)

# ============================
# MQTT defaults
# ============================
broker = "broker.mqttdashboard.com"
port = 1883

# ============================
# Variables / session_state
# ============================
if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False
