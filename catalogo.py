import streamlit as st
from supabase import Client


def mostrar_modulo_catalogo(supabase: Client):
  st.title("📦 Catálogo de Productos Frecuentes")
  st.write(
      "Administra tus plantillas de productos recurrentes (como llaveros, figuras,"
      " etc.) para cargarlos rápidamente al registrar ventas."
  )

  # Pestañas para organizar la vista y el alta
  tab_lista, tab_nuevo = st.tabs(
      ["📋 Ver Catálogo", "➕ Agregar Nuevo Producto"]
  )

  # --- PESTAÑA 1: VER Y EDITAR/BORRAR CATÁLOGO ---
  with tab_lista:
    st.subheader("Productos Registrados")
    try:
      response = supabase.table("catalogo_productos").select("*").execute()
      productos = response.data

      if not productos:
        st.info("Aún no tienes productos guardados en el catálogo.")
      else:
        for prod in productos:
          with st.expander(
              f"🏷️ {prod['nombre_producto']} — Precio:"
              f" ${prod.get('precio_sugerido', 0)}"
          ):
            col1, col2 = st.columns(2)
            with col1:
              st.write(
                  f"**Material Sugerido:**"
                  f" {prod.get('material_sugerido', 'N/A')}"
              )
              st.write(
                  f"**Color Sugerido:** {prod.get('color_sugerido', 'N/A')}"
              )
              st.write(
                  f"**Peso Sugerido:** {prod.get('peso_gramos_sugerido', 0)} g"
              )
            with col2:
              st.write(
                  f"**Tiempo Estimado:**"
                  f" {prod.get('tiempo_horas_sugerido', 0)} hrs"
              )
              if prod.get("imagen_url"):
                st.write(f"**Imagen/URL:** {prod.get('imagen_url')}")

            # Botón para eliminar del catálogo
            if st.button(
                f"🗑️ Eliminar '{prod['nombre_producto']}'", key=f"del_{prod['id']}"
            ):
              try:
                supabase.table("catalogo_productos").delete().eq(
                    "id", prod["id"]
                ).execute()
                st.success(f"Producto '{prod['nombre_producto']}' eliminado.")
                st.rerun()
              except Exception as e:
                st.error(f"Error al eliminar: {e}")

    except Exception as e:
      st.error(f"Error al cargar el catálogo: {e}")

  # --- PESTAÑA 2: AGREGAR NUEVO PRODUCTO ---
  with tab_nuevo:
    st.subheader("Registrar Nueva Plantilla de Producto")

    with st.form("form_nuevo_producto"):
      nombre = st.text_input(
          "Nombre del Producto (Ej. Llavero Templo Mormón)"
      )
      col_a, col_b = st.columns(2)
      with col_a:
        material = st.text_input("Material Sugerido (Ej. PLA, PETG)")
        peso = st.number_input(
            "Peso Sugerido (gramos)", min_value=0.0, format="%.2f"
        )
        precio = st.number_input(
            "Precio de Venta Sugerido ($)", min_value=0.0, format="%.2f"
        )
      with col_b:
        color = st.text_input("Color Sugerido (Ej. Blanco, Negro)")
        tiempo = st.number_input(
            "Tiempo Estimado (horas)", min_value=0.0, format="%.2f"
        )
        imagen = st.text_input(
            "URL de Imagen (Opcional para futuras cotizaciones)"
        )

      submitted = st.form_submit_button("Guardar en el Catálogo")

      if submitted:
        if not nombre:
          st.warning("El nombre del producto es obligatorio.")
        else:
          try:
            nuevo_prod = {
                "nombre_producto": nombre,
                "material_sugerido": material,
                "color_sugerido": color,
                "peso_gramos_sugerido": peso,
                "tiempo_horas_sugerido": tiempo,
                "precio_sugerido": precio,
                "imagen_url": imagen,
            }
            supabase.table("catalogo_productos").insert(nuevo_prod).execute()
            st.success(
                f"¡Producto '{nombre}' agregado al catálogo exitosamente!"
            )
            st.rerun()
          except Exception as e:
            st.error(f"Error al guardar el producto: {e}")