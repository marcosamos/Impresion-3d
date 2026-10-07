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


def cargar_catalogo():
  response = supabase.table("catalogo_productos").select("*").execute()
  data = response.data
  if data:
    return pd.DataFrame(data)
  else:
    return pd.DataFrame()


def mostrar_modulo_ventas(ultimo_calculo=None):
  st.title("📊 Historial y Control de Ventas")
  st.write(
      "Registra tus pedidos. Ve armando tu carrito de productos y filamentos,"
      " ajusta lo necesario y confirma la venta cuando esté lista."
  )

  # Inicializar estados de sesión
  if "materiales_venta" not in st.session_state:
    st.session_state.materiales_venta = []
  if "productos_venta" not in st.session_state:
    st.session_state.productos_venta = []

  df_inv = cargar_inventario()
  df_cat = cargar_catalogo()

  st.subheader("🛒 1. Armar Carrito de Productos")

  # --- SECCIÓN PARA AGREGAR PRODUCTOS UNO A UNO ---
  with st.container():
    col_p1, col_p2, col_p3, col_p4 = st.columns([2, 1, 1, 1])

    opciones_catalogo = ["-- Escribir libre o elegir del catálogo --"]
    if not df_cat.empty:
      opciones_catalogo += df_cat["nombre_producto"].tolist()

    with col_p1:
      prod_elegido_cat = st.selectbox(
          "Producto del catálogo (Opcional)",
          opciones_catalogo,
          key="sel_prod_carrito",
      )

      def_nombre = ""
      def_precio = 0.0
      def_gramos = 30.0

      if prod_elegido_cat != "-- Escribir libre o elegir del catálogo --":
        p_info = df_cat[df_cat["nombre_producto"] == prod_elegido_cat].iloc[0]
        def_nombre = p_info["nombre_producto"]
        def_precio = float(p_info.get("precio_sugerido", 0.0))
        def_gramos = float(p_info.get("peso_gramos_sugerido", 30.0))
      elif ultimo_calculo and isinstance(ultimo_calculo, dict):
        def_nombre = ultimo_calculo.get("producto", "")
        def_precio = float(ultimo_calculo.get("precio_final", 0.0))
        def_gramos = float(ultimo_calculo.get("gramos", 30.0))

      nombre_prod_input = st.text_input(
          "Nombre del producto/pieza",
          value=def_nombre,
          key="input_nombre_prod",
      )

    with col_p2:
      cantidad_prod = st.number_input(
          "Cantidad", min_value=1, value=1, step=1, key="input_cant_prod"
      )

    with col_p3:
      precio_unit_input = st.number_input(
          "Precio Unitario ($)",
          min_value=0.0,
          value=def_precio,
          step=10.0,
          key="input_precio_prod",
      )

    with col_p4:
      st.text("")
      st.text("")
      btn_agregar_carrito = st.button("➕ Añadir al carrito")

    if btn_agregar_carrito:
      if nombre_prod_input and precio_unit_input >= 0:
        st.session_state.productos_venta.append({
            "Producto": nombre_prod_input,
            "Cantidad": int(cantidad_prod),
            "Precio_Unitario": float(precio_unit_input),
            "Subtotal": float(cantidad_prod * precio_unit_input),
            "Gramos_Estimados": float(def_gramos * cantidad_prod),
        })
        st.success(
            f"Añadido: {cantidad_prod}x {nombre_prod_input} al carrito."
        )
        st.rerun()
      else:
        st.error("Indica un nombre de producto válido y un precio.")

    # Mostrar tabla del carrito actual
    total_calculado_carrito = 0.0
    if st.session_state.productos_venta:
      st.markdown("**Productos en este ticket actual:**")
      df_carrito = pd.DataFrame(st.session_state.productos_venta)
      st.dataframe(df_carrito, use_container_width=True)

      total_calculado_carrito = sum(
          item["Subtotal"] for item in st.session_state.productos_venta
      )
      st.metric(
          "💰 Subtotal del Carrito", f"${total_calculado_carrito:,.2f} MXN"
      )

      if st.button("🗑️ Vaciar carrito de productos"):
        st.session_state.productos_venta = []
        st.rerun()
    else:
      st.info(
          "🛒 El carrito está vacío. Agrega tus productos uno a uno (ej. el"
          " honguito y luego el tubo verde)."
      )

  st.markdown("---")

  # --- SECCIÓN DE FILAMENTOS ---
  st.subheader("🧵 2. Filamentos Utilizados")

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
      sugerencia_gramos_totales = sum(
          item["Gramos_Estimados"] for item in st.session_state.productos_venta
      )
      if sugerencia_gramos_totales <= 0:
        sugerencia_gramos_totales = 30.0

      gramos_parciales = st.number_input(
          "Gramos gastados de este rollo",
          min_value=1.0,
          value=float(sugerencia_gramos_totales),
          step=5.0,
      )
    with col_sel3:
      st.text("")
      st.text("")
      btn_agregar_material = st.button("➕ Añadir filamento gastado")

    if btn_agregar_material:
      nombre_rollo_str = df_inv[df_inv["ID_Rollo"] == rollo_elegido][
          "Nombre"
      ].values[0]
      st.session_state.materiales_venta.append({
          "ID_Rollo": rollo_elegido,
          "Nombre_Rollo": nombre_rollo_str,
          "Gramos": gramos_parciales,
      })
      st.success(f"Añadidos {gramos_parciales}g del rollo {rollo_elegido}.")
      st.rerun()

    if st.session_state.materiales_venta:
      st.markdown("**Materiales agregados:**")
      df_temp_mat = pd.DataFrame(st.session_state.materiales_venta)
      st.dataframe(df_temp_mat, use_container_width=True)

      if st.button("🗑️ Limpiar lista de filamentos"):
        st.session_state.materiales_venta = []
        st.rerun()
    else:
      st.info(
          "Aún no registras filamentos gastados. Añade los rollos que ocupó el"
          " trabajo."
      )
  else:
    st.warning("⚠️ No hay rollos activos en el inventario.")

  st.markdown("---")

  # --- SECCIÓN FINAL: CLIENTE Y CONFIRMACIÓN DE VENTA ---
  st.subheader("📝 3. Datos del Cliente y Confirmación")

  c_cli1, c_cli2 = st.columns(2)
  with c_cli1:
    cliente = st.text_input("Nombre del Cliente (ej. Eduardo)")
  with c_cli2:
    gramos_acumulados_calc = sum(
        item["Gramos"] for item in st.session_state.materiales_venta
    )
    st.metric("Gramos Totales Gastados", f"{gramos_acumulados_calc:,.1f} g")

  # Permitir ajustar el precio final total si se desea aplicar descuento o ajuste
  total_venta = st.number_input(
      "Precio Final Total Cobrado ($ MXN)",
      min_value=0.0,
      value=float(total_calculado_carrito),
      step=10.0,
  )

  st.markdown("")
  if st.button(
      "🚀 Confirmar Venta y Descontar Stock",
      type="primary",
      use_container_width=True,
  ):
    if cliente and st.session_state.productos_venta and total_venta >= 0:
      df_ventas = cargar_ventas()
      nuevo_folio = len(df_ventas) + 1
      folio_str = f"V-{nuevo_folio:03d}"

      productos_str = ", ".join([
          f"{p['Cantidad']}x {p['Producto']}"
          for p in st.session_state.productos_venta
      ])

      if st.session_state.materiales_venta:
        desc_rollos = ", ".join([
            f"{m['ID_Rollo']} ({m['Gramos']}g)"
            for m in st.session_state.materiales_venta
        ])
      else:
        desc_rollos = "Ninguno"

      costo_produccion_calc = round(gramos_acumulados_calc * 0.5, 2)
      ganancia_neta_calc = total_venta - costo_produccion_calc

      datos_venta = {
          "Folio": folio_str,
          "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
          "Cliente": cliente,
          "Producto": productos_str,
          "Costo_Produccion": round(costo_produccion_calc, 2),
          "Precio_Venta": round(total_venta, 2),
          "Ganancia_Neta": round(ganancia_neta_calc, 2),
          "Estatus": "Completado",
          "Gramos": gramos_acumulados_calc,
          "Rollo_Usado": desc_rollos,
          "Total": round(total_venta, 2),
          "Estado": "Completado",
          "Gramos_Totales": gramos_acumulados_calc,
          "Rollos_Usados": desc_rollos,
      }
      guardar_venta(datos_venta)

      # Descontar inventario en Supabase
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

      # Limpiar estados tras guardar con éxito
      st.session_state.materiales_venta = []
      st.session_state.productos_venta = []
      st.success(
          f"¡Venta múltiple {folio_str} registrada con éxito y stock"
          " descontado!"
      )
      st.rerun()
    else:
      st.error(
          "Por favor escribe el nombre del cliente y asegúrate de agregar"
          " al menos un producto al carrito."
      )

  st.markdown("---")
  st.subheader("📋 Historial de Ventas")
  df_ventas = cargar_ventas()

  if not df_ventas.empty:
    df_ventas["Total"] = pd.to_numeric(
        df_ventas["Total"], errors="coerce"
    ).fillna(0.0)
    total_ingresos = float(df_ventas["Total"].sum())

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