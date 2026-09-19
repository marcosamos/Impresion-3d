import pandas as pd
import streamlit as st
from supabase import create_client


@st.cache_resource
def init_supabase():
  url = st.secrets["supabase"]["url"]
  key = st.secrets["supabase"]["key"]
  return create_client(url, key)


supabase = init_supabase()


def cargar_inventario():
  response = supabase.table("inventario").select("*").execute()
  data = response.data
  if data:
    df = pd.DataFrame(data)
    if "Color" not in df.columns:
      df["Color"] = "General"
    return df
  else:
    return pd.DataFrame(columns=[
        "ID_Rollo",
        "Nombre",
        "Material",
        "Color",
        "Gramos_Iniciales",
        "Gramos_Actuales",
        "Costo",
        "Proveedor",
        "Estado",
    ])


def mostrar_modulo_inventario():
  st.title("📦 Control de Inventario y Rollos de Filamento")
  st.write(
      "Supervisa el estado de tus rollos y mantén tu política de respaldo de"
      " 1000g por color al día."
  )

  df_inv = cargar_inventario()

  if not df_inv.empty:
    df_inv.columns = df_inv.columns.str.strip()

    activos = (
        df_inv[
            df_inv["Estado"].astype(str).str.strip().str.capitalize() == "Activo"
        ]
        if "Estado" in df_inv.columns
        else df_inv
    )

    total_rollos = len(activos)
    gramos_totales = (
        activos["Gramos_Actuales"].sum() if not activos.empty else 0
    )

    m1, m2 = st.columns(2)
    m1.metric("🧵 Rollos Activos en Estante", f"{total_rollos}")
    m2.metric(
        "⚖️ Filamento Total Disponible",
        f"{gramos_totales:,.0f} g ({gramos_totales/1000:.2f} kg)",
    )

    # --- CONTROL DE MÍNIMOS Y RESPALDO (1000g por Material + Color) ---
    st.markdown("---")
    st.subheader("🚨 Alertas de Stock y Respaldo por Color")
    st.write(
        "Política de respaldo: Mínimo **1000 gramos (1 rollo)** disponible por"
        " cada combinación de Material y Color."
    )

    if not activos.empty:
      if "Color" not in activos.columns:
        activos["Color"] = "General"

      resumen_stock = (
          activos.groupby(["Material", "Color"])["Gramos_Actuales"]
          .sum()
          .reset_index()
      )

      MINIMO_REQUERIDO = 1000.0
      alertas_activas = []

      for _, row in resumen_stock.iterrows():
        mat = row["Material"]
        col = row["Color"]
        gramos_actuales = row["Gramos_Actuales"]

        if gramos_actuales < MINIMO_REQUERIDO:
          alertas_activas.append((mat, col, gramos_actuales))

      if alertas_activas:
        for mat, col, gramos in alertas_activas:
          st.error(
              f"⚠️ **¡Stock bajo de respaldo!** El filamento **{mat} - {col}**"
              f" tiene un total de **{gramos:,.0f} g** en el estante (Por debajo"
              f" del mínimo de {MINIMO_REQUERIDO:,.0f}g). ¡Urge reponer"
              " respaldo!"
          )
      else:
        st.success(
            "✅ ¡Todo en orden! Tienes el respaldo cubierto (más de 1000g) en"
            " todos tus materiales y colores activos."
        )
    else:
      st.info("No hay rollos activos para evaluar el respaldo.")

    st.markdown("---")
    st.subheader("📋 Estado Actual de tus Rollos")
    st.dataframe(df_inv, use_container_width=True)

    # --- OPCIONES AVANZADAS: AJUSTAR Y ELIMINAR ROLLOS ---
    with st.expander("⚙️ Opciones avanzadas, Ajuste y Eliminación"):
      st.markdown("### 🛠️ Modificar Estado o Gramos")
      rollo_editar = st.selectbox(
          "Selecciona un rollo para modificar",
          df_inv["ID_Rollo"].tolist(),
          key="sel_editar_rollo",
      )

      idx = df_inv[df_inv["ID_Rollo"] == rollo_editar].index[0]
      gramos_actuales_rollo = float(df_inv.loc[idx, "Gramos_Actuales"])
      estado_actual_rollo = str(df_inv.loc[idx, "Estado"])

      c_adj1, c_adj2 = st.columns(2)
      with c_adj1:
        nuevo_gramaje = st.number_input(
            "Ajustar Gramos Actuales",
            min_value=0.0,
            value=gramos_actuales_rollo,
            step=10.0,
        )
      with c_adj2:
        estados_posibles = ["Activo", "Terminado", "Pausado"]
        indice_estado = (
            estados_posibles.index(estado_actual_rollo)
            if estado_actual_rollo in estados_posibles
            else 0
        )
        nuevo_estado = st.selectbox(
            "Nuevo Estado", estados_posibles, index=indice_estado
        )

      if st.button("Guardar Cambios del Rollo"):
        if nuevo_gramaje <= 0 and nuevo_estado == "Activo":
          nuevo_estado = "Terminado"

        supabase.table("inventario").update({
            "Gramos_Actuales": nuevo_gramaje,
            "Estado": nuevo_estado,
        }).eq("ID_Rollo", rollo_editar).execute()

        st.success(
            f"El rollo {rollo_editar} se actualizó correctamente ({nuevo_gramaje}g"
            f" - {nuevo_estado})."
        )
        st.rerun()

      st.markdown("---")
      st.markdown("### 🗑️ Eliminar Rollo por Completo")
      rollo_borrar = st.selectbox(
          "Selecciona el rollo a eliminar permanentemente",
          df_inv["ID_Rollo"].tolist(),
          key="sel_borrar_rollo",
      )

      if st.button("Eliminar este rollo de la base de datos"):
        supabase.table("inventario").delete().eq(
            "ID_Rollo", rollo_borrar
        ).execute()
        st.success(
            f"El rollo {rollo_borrar} ha sido eliminado por completo del"
            " inventario."
        )
        st.rerun()
  else:
    st.info(
        "Aún no hay rollos en el inventario. Ve al módulo de **Control de"
        " Compras** y da de alta rollos."
    )