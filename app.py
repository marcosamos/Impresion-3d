from calculadora import mostrar_calculadora
from compras import mostrar_modulo_compras
from inventario import mostrar_modulo_inventario
from ventas import mostrar_modulo_ventas
import streamlit as st

st.set_page_config(
    page_title="Sistema 3D Profesional", page_icon="🖨️", layout="wide"
)

# --- MENÚ DE NAVEGACIÓN LATERAL ---
st.sidebar.title("🖨️ Menú Principal")
menu = st.sidebar.radio(
    "Selecciona una opción:",
    [
        "🧮 Calculadora de Precios",
        "📊 Historial y Control de Ventas",
        "🛒 Control de Compras",
        "📦 Control de Inventario",
    ],
)

if "ultimo_calculo" not in st.session_state:
  st.session_state.ultimo_calculo = None

if menu == "🧮 Calculadora de Precios":
  resultado = mostrar_calculadora()
  if resultado:
    st.session_state.ultimo_calculo = resultado

elif menu == "📊 Historial y Control de Ventas":
  mostrar_modulo_ventas(st.session_state.ultimo_calculo)

elif menu == "🛒 Control de Compras":
  mostrar_modulo_compras()

elif menu == "📦 Control de Inventario":
  mostrar_modulo_inventario()