import paho.mqtt.client as paho
import time
import streamlit as st
import json
import platform
import random



#FONDO 
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

# Usa la imagen
set_background("fondo.png")   # ← Asegúrate que esté en la misma carpeta


# Muestra la versión de Python junto con detalles adicionales
st.write("Versión de Python:", platform.python_version())




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

        


broker="157.230.214.127"
port=1883
client1= paho.Client("STREAMLIT_MYSTIC_PUB")
client1.on_message = on_message



st.title("Buena suerte")


if st.button('suerte'):

    values = random.choice([30, 45, 150])
    st.write('Values:', values)


    client1= paho.Client("GIT-HUB")                           
    client1.on_publish = on_publish                          
    client1.connect(broker,port)   
    message =json.dumps({"Analog": float(values)})
    ret= client1.publish("cmqtt_a", message)
    
 
else:
    st.write('')
