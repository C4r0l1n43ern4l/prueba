# app.py
# Aquí va el código principal del prototipo agrícola con Streamlit
# Una vez pegue el código completo aquí, podrá ejecutar: streamlit run app.py

import streamlit as st
import pandas as pd
import requests
import firebase_admin
from firebase_admin import credentials, firestore, auth
from cryptography.fernet import Fernet
import datetime

# --- Inicialización Firebase ---
if not firebase_admin._apps:
    cred = credentials.Certificate(1234)
    firebase_admin.initialize_app(cred)
db = firestore.client()

# --- Utilidades de Cifrado ---
fernet = Fernet(st.secrets[1234])

# --- Autenticación ---
def login():
    st.sidebar.header("Autenticación")
    choice = st.sidebar.selectbox("¿Tienes cuenta?", ["Iniciar Sesión", "Registrarse"])

    if choice == "Registrarse":
        email = st.sidebar.text_input("Email")
        password = st.sidebar.text_input("Contraseña", type="password")
        pregunta = st.sidebar.text_input("Nombre de su primera finca")
        if st.sidebar.button("Crear cuenta"):
            try:
                user = auth.create_user(email=email, password=password)
                db.collection("usuarios").document(email).set({
                    "pregunta": fernet.encrypt(pregunta.encode()).decode()
                })
                st.sidebar.success("Usuario registrado. Ahora inicia sesión.")
            except:
                st.sidebar.error("Error al registrar")

    elif choice == "Iniciar Sesión":
        email = st.sidebar.text_input("Email")
        password = st.sidebar.text_input("Contraseña", type="password")
        if st.sidebar.button("Iniciar"):
            try:
                auth.get_user_by_email(email)
                st.session_state["usuario"] = email
                st.sidebar.success("Sesión iniciada")
            except:
                st.sidebar.error("Credenciales inválidas")

# --- Chatbot Simple ---
def chatbot_respuesta(pregunta):
    respuestas = {
        "fertilizante": "Para papa: use nitrógeno cada 2 semanas.",
        "riego": "Riegue temprano en la mañana o al atardecer.",
        "plagas": "Use pesticidas naturales como neem."
    }
    for palabra, respuesta in respuestas.items():
        if palabra in pregunta.lower():
            return respuesta
    return "No tengo una respuesta para eso aún."

# --- Sección: Clima ---
def mostrar_clima():
    st.subheader("🌦️ Información Climática")
    municipio = st.selectbox("Selecciona municipio", ["Bogotá", "Medellín", "Cali", "Barranquilla"])
    api_key = st.secrets["OWM_KEY"]
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={municipio},CO&units=metric&appid={api_key}"
        response = requests.get(url)
        data = response.json()
        if response.status_code == 200:
            st.write(f"Temperatura: {data['main']['temp']}°C")
            st.write(f"Humedad: {data['main']['humidity']}%")
            clima = data['weather'][0]['description']
            st.write(f"Condición: {clima}")
            if "rain" in clima:
                st.warning("⚠️ Alerta: Posibilidad de lluvias intensas.")
        else:
            st.error("No se pudo obtener el clima.")
    except:
        st.error("Error al conectar con el servicio climático.")

# --- Sección: Precios Agrícolas ---
def mostrar_precios():
    st.subheader("📈 Precios Agrícolas")
    # Simulamos datos
    data = {
        "Fecha": pd.date_range(start="2024-01-01", periods=10, freq="M"),
        "Papa": [1800, 1900, 2000, 2100, 2200, 2300, 2400, 2300, 2200, 2100],
        "Café": [9000, 9200, 9100, 9300, 9400, 9500, 9600, 9550, 9600, 9700]
    }
    df = pd.DataFrame(data).set_index("Fecha")
    st.line_chart(df)

# --- Sección: Registro de Cosecha ---
def registrar_cosecha(usuario):
    st.subheader("📝 Registro de Cosecha")
    cultivo = st.selectbox("Tipo de cultivo", ["Papa", "Café", "Maíz"])
    cantidad = st.number_input("Cantidad (kg)", min_value=0)
    fecha = st.date_input("Fecha", value=datetime.date.today())

    if st.button("Registrar"):
        try:
            registro = {
                "cultivo": cultivo,
                "cantidad": fernet.encrypt(str(cantidad).encode()).decode(),
                "fecha": fecha.isoformat(),
                "usuario": usuario
            }
            db.collection("cosechas").add(registro)
            st.success("Cosecha registrada exitosamente.")
        except:
            st.error("Error al registrar la cosecha.")

# --- Sección: Recomendaciones ---
def mostrar_recomendaciones():
    st.subheader("🌱 Recomendaciones")
    if st.button("Fertilizante para papa"):
        st.info("Para papa se recomienda nitrógeno y fósforo cada 15 días.")
    if st.button("Control de plagas para café"):
        st.info("Utilice trampas de luz y control biológico.")

# --- Sección: Chatbot ---
def mostrar_chatbot():
    st.subheader("🤖 Asistente Agrícola")
    pregunta = st.text_input("Haz una pregunta:")
    if st.button("Enviar"):
        respuesta = chatbot_respuesta(pregunta)
        st.write(f"Respuesta: {respuesta}")

# --- Main App ---
st.set_page_config(page_title="Agro Dashboard", layout="wide")
st.title("🌾 Dashboard Agrícola")

if "usuario" not in st.session_state:
    login()
else:
    seccion = st.sidebar.radio("Menú", ["Clima", "Precios", "Registro Cosecha", "Recomendaciones", "Chatbot"])
    if seccion == "Clima":
        mostrar_clima()
    elif seccion == "Precios":
        mostrar_precios()
    elif seccion == "Registro Cosecha":
        registrar_cosecha(st.session_state["usuario"])
    elif seccion == "Recomendaciones":
        mostrar_recomendaciones()
    elif seccion == "Chatbot":
        mostrar_chatbot()
