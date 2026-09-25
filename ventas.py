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


def cargar_ventas():
  response = supabase.table("ventas").select("*").execute()
  data = response.data
  if data:
    return pd.DataFrame(data)
  else:
    return pd.DataFrame(columns=[
        "Folio",
        "Fecha",
        "Cliente",
        "Producto",
        "Gramos_Totales",
        "Rollos_Usados",
        "Total",
        "Estado",
    ])


def guardar_venta(nueva_venta):
  supabase.table("ventas").insert(nueva_venta).execute()


def cargar_inventario():
  response = supabase.table("inventario").select("*").execute()
  data = response.data
  if data:
    return pd.DataFrame(data)
  else:
    return pd.DataFrame()


def mostrar_modulo_ventas(ultimo_calculo=None):
  st.title("📊 Historial y Control de Ventas")
  st.write(
      "Registra tus pedidos. Si usas varios colores o rollos, puedes añadirlos"
      " todos a la venta y el sistema descontará el stock de cada uno."
  )

  if "materiales_venta" not in st.session_state:
    st.session_state.materiales_venta = []

  df_inv = cargar_inventario()

  st.subheader("Registrar Nueva Venta")

  # --- 1. SECCIÓN DE MÚLTIPLES ROLLOS (CONSUMO MULTICOLOR) ---
  st.markdown("### 🧵 1. Filamentos Utilizados en este Pedido")

  rollos_disponibles = []
  if not df_inv.empty:
    df_inv.columns = df_inv.columns.str.strip()
    if "Estado" in df_inv.columns:
      df_activos = df_inv[
          df_inv["Estado"].astype(str).str.strip().str.capitalize() == "Activo"
      ]
      rollos_disponibles = df_activos["ID_Rollo"].tolist()
    else:
      rollos_disponibles = df_inv["ID_Rollo"].tolist()

  if rollos_disponibles:
    col_sel1, col_sel2, col_sel3 = st.columns([2, 1, 1])
    with col_sel1:
      rollo_elegido = st.selectbox(
          "Selecciona el rollo",
          rollos_disponibles,
          format_func=lambda x: (
              f"{x} - {df_inv[df_inv['ID_Rollo'] == x]['Nombre'].values[0]}"
              f" (Quedan: {df_inv[df_inv['ID_Rollo'] == x]['Gramos_Actuales'].values[0]}g)"
          ),
      )
    with col_sel2:
      gramos_parciales = st.number_input(
          "Gramos gastados de este rollo",
          min_value=1.0,
          value=30.0,
          step=5.0,
      )
    with col_sel3:
      st.text("")
      st.text("")
      btn_agregar_material = st.button("➕ Añadir al pedido")

    if btn_agregar_material:
      nombre_rollo_str = df_inv[df_inv["ID_Rollo"] == rollo_elegido][
          "Nombre"
      ].values[0]
      st.session_state.materiales_venta.append({
          "ID_Rollo": rollo_elegido,
          "Nombre_Rollo": nombre_rollo_str,
          "Gramos": gramos_parciales,
      })
      st.success(
          f"Añadidos {gramos_parciales}g del rollo {rollo_elegido} al pedido."
      )
      st.rerun()

    if st.session_state.materiales_venta:
      st.markdown("**Materiales agregados a esta venta:**")
      df_temp_mat = pd.DataFrame(st.session_state.materiales_venta)
      st.dataframe(df_temp_mat, use_container_width=True)

      if st.button("🗑️ Limpiar lista de materiales"):
        st.session_state.materiales_venta = []
        st.rerun()
    else:
      st.info(
          "Aún no agregas ningún rollo. Selecciona los rollos y gramos que"
          " gastó la impresión."
      )
  else:
    st.warning("⚠️ No hay rollos activos en el inventario para seleccionar.")

  st.markdown("---")

  # --- 2. FORMULARIO DE DATOS DE LA VENTA ---
  with st.form("form_registrar_venta"):
    st.markdown("### 📝 2. Datos del Cliente y Cobro")
    c1, c2 = st.columns(2)

    with c1:
      cliente = st.text_input("Nombre del Cliente")
      producto = st.text_input(
          "Producto / Pieza vendida",
          value=(
              ultimo_calculo.get("producto", "")
              if ultimo_calculo and isinstance(ultimo_calculo, dict)
              else ""
          ),
      )
    with c2:
      gramos_acumulados_calc = sum(
          item["Gramos"] for item in st.session_state.materiales_venta
      )
      if gramos_acumulados_calc == 0 and ultimo_calculo and isinstance(
          ultimo_calculo, dict
      ):
        gramos_acumulados_calc = ultimo_calculo.get("gramos", 50.0)
      elif gramos_acumulados_calc == 0:
        gramos_acumulados_calc = 50.0

      st.metric(
          "Gramos Totales Acumulados", f"{gramos_acumulados_calc:,.1f} g"
      )

      precio_sugerido = (
          ultimo_calculo.get("precio_final", 0.0)
          if ultimo_calculo and isinstance(ultimo_calculo, dict)
          else 0.0
      )
      total_venta = st.number_input(
          "Precio Final Cobrado ($ MXN)",
          min_value=0.0,
          value=float(precio_sugerido),
          step=10.0,
      )

    btn_guardar_venta = st.form_submit_button("Confirmar Venta y Descontar Stock")

    if btn_guardar_venta:
      if cliente and producto and total_venta > 0:
        df_ventas = cargar_ventas()
        nuevo_folio = len(df_ventas) + 1
        folio_str = f"V-{nuevo_folio:03d}"

        if st.session_state.materiales_venta:
          desc_rollos = ", ".join([
              f"{m['ID_Rollo']} ({m['Gramos']}g)"
              for m in st.session_state.materiales_venta
          ])
        else:
          desc_rollos = "Ninguno"

        # Extraemos el desglose del último cálculo con seguridad
        calc = (
            ultimo_calculo
            if ultimo_calculo and isinstance(ultimo_calculo, dict)
            else {}
        )

        datos_venta = {
            "Folio": folio_str,
            "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Cliente": cliente,
            "Producto": producto,
            "Costo_Produccion": calc.get("costo_produccion", 0.0),
            "Precio_Venta": calc.get("precio_final", 0.0),
            "Ganancia_Neta": calc.get("ganancia_neta", 0.0),
            "Estatus": "Completado",
            "Gramos": gramos_acumulados_calc,
            "Rollo_Usado": desc_rollos,
            "Total": round(total_venta, 2),
            "Estado": "Completado",
            "Gramos_Totales": gramos_acumulados_calc,
            "Rollos_Usados": desc_rollos,
        }
        guardar_venta(datos_venta)

        # Descontar del inventario en Supabase cada rollo usado
        if st.session_state.materiales_venta:
          for item in st.session_state.materiales_venta:
            id_r = item["ID_Rollo"]
            g_gasto = item["Gramos"]

            res = (
                supabase.table("inventario")
                .select("Gramos_Actuales, Estado")
                .eq("ID_Rollo", id_r)
                .execute()
            )
            if res.data:
              actuales = float(res.data[0]["Gramos_Actuales"])
              nuevo_total = max(0.0, actuales - g_gasto)
              nuevo_estado = (
                  "Terminado" if nuevo_total <= 0 else res.data[0]["Estado"]
              )

              supabase.table("inventario").update({
                  "Gramos_Actuales": nuevo_total,
                  "Estado": nuevo_estado,
              }).eq("ID_Rollo", id_r).execute()

        st.session_state.materiales_venta = []
        st.success(
            f"¡Venta {folio_str} registrada con éxito y stock descontado!"
        )
        st.rerun()
      else:
        st.error(
            "Por favor llena el cliente, el producto, un precio mayor a 0 y"
            " asegúrate de añadir los materiales."
        )

  st.markdown("---")
  st.subheader("📋 Historial de Ventas")
  df_ventas = cargar_ventas()

  if not df_ventas.empty:
    total_ingresos = df_ventas["Total"].sum()
    total_ingresos = float(total_ingresos) if pd.notna(total_ingresos) else 0.0

    m1, m2 = st.columns(2)
    m1.metric("📦 Ventas Totales", f"{len(df_ventas)}")
    m2.metric("💰 Ingresos Acumulados", f"${total_ingresos:,.2f} MXN")

    st.dataframe(df_ventas, use_container_width=True)

    with st.expander("🗑️ Eliminar una venta por error (Devuelve Stock)"):
      folio_borrar = st.selectbox(
          "Selecciona el Folio de venta a eliminar",
          df_ventas["Folio"].tolist(),
          key="sel_folio_borrar",
      )
      if st.button("Eliminar esta venta y regresar materiales"):
        venta_a_borrar = df_ventas[df_ventas["Folio"] == folio_borrar]

        if not venta_a_borrar.empty:
          rollos_str = str(venta_a_borrar.iloc[0]["Rollos_Usados"])

          if rollos_str != "Ninguno" and rollos_str.strip() != "":
            partes = rollos_str.split(",")
            for parte in partes:
              if "(" in parte and ")" in parte:
                id_r = parte.split("(")[0].strip()
                g_str = parte.split("(")[1].split("g")[0].strip()
                try:
                  g_dev = float(g_str)
                  res = (
                      supabase.table("inventario")
                      .select("Gramos_Actuales")
                      .eq("ID_Rollo", id_r)
                      .execute()
                  )
                  if res.data:
                    actuales = float(res.data[0]["Gramos_Actuales"])
                    supabase.table("inventario").update({
                        "Gramos_Actuales": actuales + g_dev,
                        "Estado": "Activo",
                    }).eq("ID_Rollo", id_r).execute()
                except ValueError:
                  pass

          supabase.table("ventas").delete().eq("Folio", folio_borrar).execute()
          st.success(
              f"Venta {folio_borrar} eliminada correctamente y materiales"
              " devueltos a sus rollos."
          )
          st.rerun()
  else:
    st.info("Aún no tienes ventas registradas.")