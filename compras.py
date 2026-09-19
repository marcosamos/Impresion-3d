from datetime import datetime
import pandas as pd
import streamlit as st
from supabase import create_client


@st.cache_resource
def init_supabase():
  url = st.secrets["supabase"]["url"]
  key = st.secrets["supabase"]["key"]
  return create_client(url, key)


supabase = init_supabase()


def cargar_compras():
  response = supabase.table("compras").select("*").execute()
  data = response.data
  if data:
    return pd.DataFrame(data)
  else:
    return pd.DataFrame(columns=[
        "Folio",
        "Fecha",
        "Articulo",
        "Categoria",
        "Cantidad",
        "Costo_Total",
        "Proveedor",
    ])


def guardar_compra(nueva_compra):
  supabase.table("compras").insert(nueva_compra).execute()


def agregar_rollo_inventario(
    nombre_rollo,
    tipo_material,
    color_principal,
    gramos_iniciales,
    costo_rollo,
    proveedor,
):
  res = supabase.table("inventario").select("ID_Rollo").execute()
  count = len(res.data) if res.data else 0
  nuevo_id = f"R-{count + 1:03d}"

  nuevo_registro = {
      "ID_Rollo": nuevo_id,
      "Nombre": nombre_rollo,
      "Material": tipo_material,
      "Color": color_principal,
      "Gramos_Iniciales": gramos_iniciales,
      "Gramos_Actuales": gramos_iniciales,
      "Costo": round(costo_rollo, 2),
      "Proveedor": proveedor,
      "Estado": "Activo",
  }
  supabase.table("inventario").insert(nuevo_registro).execute()


def mostrar_modulo_compras():
  st.title("🛒 Control de Compras y Gastos")
  st.write(
      "Registra tus adquisiciones de filamento, insumos y gastos operativos."
  )

  # --- SECCIÓN 1: REGISTRAR GASTO GENERAL ---
  with st.form("form_registrar_compra", clear_on_submit=True):
    st.subheader("1️⃣ Registrar Ticket de Compra (Gasto)")
    c1, c2 = st.columns(2)
    with c1:
      articulo = st.text_input(
          "Descripción general (ej. Pack 6 rollos PLA o Imanes N52)"
      )
      categoria = st.selectbox(
          "Categoría",
          [
              "Filamento",
              "Insumo / Extra (Imanes, LEDs, etc.)",
              "Empaque",
              "Mantenimiento / Máquina",
              "Otro",
          ],
      )
    with c2:
      cantidad = st.number_input(
          "Cantidad total de artículos/paquetes",
          min_value=1,
          value=1,
          step=1,
      )
      costo_total = st.number_input(
          "Costo Total del Ticket ($ MXN)", min_value=0.0, value=0.0, step=10.0
      )

    proveedor = st.text_input("Proveedor (ej. MercadoLibre, Amazon, Steren)")
    btn_guardar_compra = st.form_submit_button("Guardar Gasto en Historial")

    if btn_guardar_compra:
      if articulo and costo_total > 0:
        df_existente = cargar_compras()
        nuevo_folio = len(df_existente) + 1
        folio_str = f"C-{nuevo_folio:03d}"

        datos_nueva_compra = {
            "Folio": folio_str,
            "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Articulo": articulo,
            "Categoria": categoria,
            "Cantidad": cantidad,
            "Costo_Total": round(costo_total, 2),
            "Proveedor": proveedor if proveedor else "No especificado",
        }
        guardar_compra(datos_nueva_compra)
        st.success(
            f"¡Compra {folio_str} registrada con éxito en tus finanzas!"
        )
        st.rerun()
      else:
        st.error("Por favor completa la descripción y un costo mayor a 0.")

  st.markdown("---")

  # --- SECCIÓN 2: ALTA DE ROLLOS CON COLORES PRINCIPALES ---
  st.subheader("2️⃣ Dar de Alta Rollos en el Inventario")
  st.write(
      "Selecciona el color principal para asegurar el control correcto de tus"
      " 1000g de respaldo."
  )

  with st.container():
    rc1, rc2, rc3 = st.columns(3)
    with rc1:
      mat_rollo = st.selectbox(
          "Material", ["PLA", "PETG", "TPU", "ABS", "ASA", "Otro"], key="input_mat"
      )
    with rc2:
      colores_principales = [
          "Blanco",
          "Negro",
          "Gris",
          "Transparente",
          "Rojo",
          "Azul",
          "Verde",
          "Amarillo",
          "Naranja",
          "Morado",
          "Rosa",
          "Dorado",
          "Plata",
          "Bronce",
          "Café / Marrón",
      ]
      color_rollo = st.selectbox(
          "Color Principal (Para Agrupación)",
          colores_principales,
          key="input_color_principal",
      )
    with rc3:
      desc_rollo = st.text_input(
          "Detalle / Marca (ej. eSun, Silk, Matte)",
          placeholder="ej. eSun Nieve",
          key="input_desc_marca",
      )

    rc4, rc5 = st.columns(2)
    with rc4:
      gramos_rollo = st.number_input(
          "Gramos del Rollo", min_value=100, value=1000, step=50, key="input_gramos"
      )
    with rc5:
      costo_rollo_ind = st.number_input(
          "Costo estimado ($ MXN)",
          min_value=0.0,
          value=250.0,
          step=10.0,
          key="input_costo",
      )

    prov_rollo = st.text_input(
        "Proveedor del rollo (opcional)",
        placeholder="ej. MercadoLibre",
        key="input_prov",
    )

    if st.button("➕ Añadir Rollo al Inventario"):
      if desc_rollo.strip() != "":
        nombre_completo = (
            f"{mat_rollo} - {color_rollo} ({desc_rollo.strip()})"
        )
        agregar_rollo_inventario(
            nombre_completo,
            mat_rollo,
            color_rollo,
            gramos_rollo,
            costo_rollo_ind,
            prov_rollo if prov_rollo else "No especificado",
        )
        st.success(
            f"¡Rollo '{nombre_completo}' ({gramos_rollo}g) guardado con éxito!"
        )
        st.rerun()
      else:
        st.error(
            "Por favor escribe el detalle o marca del rollo (ej. eSun, Matte)."
        )

  # --- SECCIÓN 3: HISTORIAL DE COMPRAS ---
  st.markdown("---")
  st.subheader("📋 Historial de Compras y Gastos")
  df_compras = cargar_compras()

  if not df_compras.empty:
    total_gastado = df_compras["Costo_Total"].sum()
    total_compras = len(df_compras)

    m1, m2 = st.columns(2)
    m1.metric("📦 Total de Compras", f"{total_compras}")
    m2.metric("💸 Gasto Total Acumulado", f"${total_gastado:,.2f} MXN")

    st.dataframe(df_compras, use_container_width=True)

    with st.expander("🗑️ Eliminar una compra por error"):
      folio_compra_borrar = st.selectbox(
          "Selecciona el Folio de compra a eliminar",
          df_compras["Folio"].tolist(),
          key="del_compra_sel",
      )
      if st.button("Eliminar esta compra"):
        supabase.table("compras").delete().eq(
            "Folio", folio_compra_borrar
        ).execute()
        st.success(f"Compra {folio_compra_borrar} eliminada correctamente.")
        st.rerun()
  else:
    st.info("Aún no tienes compras o gastos registrados.")