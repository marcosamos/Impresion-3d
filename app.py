from calculadora import mostrar_calculadora
from compras import mostrar_modulo_compras
from inventario import mostrar_modulo_inventario
from ventas import mostrar_modulo_ventas
import streamlit as st
from supabase import create_client

st.set_page_config(
    page_title="Sistema 3D Profesional", page_icon="🖨️", layout="wide"
)


# --- CONEXIÓN A SUPABASE PARA AUTENTICACIÓN ---
@st.cache_resource
def init_supabase_auth():
  url = st.secrets["supabase"]["url"]
  key = st.secrets["supabase"]["key"]
  return create_client(url, key)


supabase = init_supabase_auth()

# --- SISTEMA DE LOGIN MULTIUSUARIO ---
if "autenticado" not in st.session_state:
  st.session_state.autenticado = False
if "usuario_actual" not in st.session_state:
  st.session_state.usuario_actual = ""

if not st.session_state.autenticado:
  st.markdown("<br><br>", unsafe_allow_html=True)
  col1, col2, col3 = st.columns([1, 2, 1])

  with col2:
    st.title("🔐 Iniciar Sesión")
    st.write("Ingresa tus credenciales para acceder al sistema.")

    with st.form("form_login"):
      usuario_input = st.text_input("Usuario")
      password_input = st.text_input("Contraseña", type="password")
      btn_ingresar = st.form_submit_button("Entrar al Sistema")

      if btn_ingresar:
        if usuario_input and password_input:
          # Consultar en Supabase si el usuario y contraseña coinciden
          response = (
              supabase.table("usuarios")
              .select("*")
              .eq("username", usuario_input)
              .eq("password", password_input)
              .execute()
          )

          if response.data and len(response.data) > 0:
            st.session_state.autenticado = True
            st.session_state.usuario_actual = usuario_input
            st.success(
                f"¡Bienvenido de nuevo, {usuario_input}! Entrando..."
            )
            st.rerun()
          else:
            st.error("Usuario o contraseña incorrectos.")
        else:
          st.warning("Por favor completa ambos campos.")

else:
  # --- MENÚ DE NAVEGACIÓN LATERAL (Usuario autenticado) ---
  st.sidebar.title("🖨️ Menú Principal")
  st.sidebar.write(f"👤 Usuario: **{st.session_state.usuario_actual}**")

  if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state.autenticado = False
    st.session_state.usuario_actual = ""
    st.rerun()

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