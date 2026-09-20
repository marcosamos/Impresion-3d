import streamlit as st


def mostrar_calculadora():
  st.title("🧮 Calculadora de Precios de Impresión 3D")
  st.write("Calcula tus costos reales y define tu precio de venta rentable.")

  col_izq, col_der = st.columns(2)

  with col_izq:
    # --- 1. MATERIAL (FILAMENTO) ---
    st.subheader("1. 🧵 Material (Filamento)")
    c1, c2 = st.columns(2)
    with c1:
      precio_rollo = st.number_input(
          "Precio del rollo ($ MXN)", min_value=0.0, value=300.0, step=20.0
      )
      peso_rollo_g = st.number_input(
          "Peso del rollo (g)", min_value=1.0, value=1000.0, step=50.0
      )
    with c2:
      peso_pieza_g = st.number_input(
          "Peso de la pieza (g)", min_value=0.1, value=00.0, step=5.0
      )
    costo_material = (precio_rollo / peso_rollo_g) * peso_pieza_g

    # --- 2. TIEMPO Y ENERGÍA ---
    st.subheader("2. ⚡ Tiempo de Impresión y Energía")
    c3, c4 = st.columns(2)
    with c3:
      horas_imp = st.number_input(
          "Horas de impresión", min_value=0, value=4, step=1
      )
      minutos_imp = st.number_input(
          "Minutos adicionales", min_value=0, max_value=59, value=0, step=5
      )
    with c4:
      consumo_watts = st.number_input(
          "Consumo de la A1 (Watts)", min_value=1.0, value=100.0, step=10.0
      )
      tarifa_kwh = st.number_input(
          "Tarifa CFE por kWh ($ MXN)", min_value=0.0, value=1.38, step=0.10
      )

    tiempo_total_horas = horas_imp + (minutos_imp / 60.0)
    costo_electricidad = (
        consumo_watts * tiempo_total_horas / 1000.0
    ) * tarifa_kwh

    # --- 3. MANO DE OBRA Y DESGASTE ---
    st.subheader("3. 🛠️ Manufactura y Desgaste")
    c5, c6 = st.columns(2)
    with c5:
      minutos_prep = st.number_input(
          "Minutos de post-proceso", min_value=0.0, value=15.0, step=5.0
      )
      valor_hora_hombre = st.number_input(
          "Valor de tu hora ($ MXN)", min_value=0.0, value=20.0, step=10.0
      )
    with c6:
      depreciacion_hora = st.number_input(
          "Desgaste de máquina/h ($ MXN)", min_value=0.0, value=2.00, step=1.00
      )
      margen_fallo = st.slider(
          "Margen por riesgo o fallo (%)", 0.0, 30.0, 10.0, step=1.0
      )

    costo_mano_obra = (minutos_prep / 60.0) * valor_hora_hombre
    costo_depreciacion = depreciacion_hora * tiempo_total_horas

    # --- 4. ARTÍCULOS EXTRA ---
    st.subheader("4. 📦 Artículos Extra e Insumos")
    if "extras" not in st.session_state:
      st.session_state.extras = []

    with st.form("form_extra", clear_on_submit=True):
      e1, e2, e3 = st.columns([3, 1, 1])
      with e1:
        nombre_extra = st.text_input("Artículo (ej. Imán, Caja)")
      with e2:
        cantidad_extra = st.number_input(
            "Cant.", min_value=1, value=1, step=1
        )
      with e3:
        costo_unitario_extra = st.number_input(
            "Costo u. ($)", min_value=0.0, value=0.0, step=1.0
        )

      submit_extra = st.form_submit_button("Agregar extra")
      if submit_extra and nombre_extra:
        st.session_state.extras.append({
            "nombre": nombre_extra,
            "cantidad": cantidad_extra,
            "costo": costo_unitario_extra * cantidad_extra,
        })

    costo_total_extras = 0.0
    if st.session_state.extras:
      for i, ext in enumerate(st.session_state.extras):
        col_l1, col_l2, col_l3 = st.columns([3, 1, 1])
        col_l1.text(f"- {ext['nombre']} (x{ext['cantidad']})")
        col_l2.text(f"${ext['costo']:.2f} MXN")
        if col_l3.button("Quitar", key=f"del_{i}"):
          st.session_state.extras.pop(i)
          st.rerun()
        costo_total_extras += ext["costo"]

    # --- 5. GANANCIA ---
    st.subheader("5. 📈 Ganancia")
    markup = st.slider("Margen de ganancia deseado (%)", 0.0, 200.0, 50.0, step=5.0)

  with col_der:
    st.subheader("📊 Resumen de Costos y Venta")

    costo_produccion = (
        costo_material
        + costo_electricidad
        + costo_mano_obra
        + costo_depreciacion
        + costo_total_extras
    )
    costo_con_riesgo = costo_produccion * (1 + margen_fallo / 100)
    precio_final = costo_con_riesgo * (1 + markup / 100)
    ganancia_neta = precio_final - costo_con_riesgo

    st.write(f"- **Costo de material:** ${costo_material:.2f} MXN")
    st.write(
        f"- **Costo energético ({horas_imp}h {minutos_imp}m):"
        f"** ${costo_electricidad:.2f} MXN"
    )
    st.write(f"- **Mano de obra:** ${costo_mano_obra:.2f} MXN")
    st.write(f"- **Desgaste de máquina:** ${costo_depreciacion:.2f} MXN")
    st.write(f"- **Artículos extra / Empaque:** ${costo_total_extras:.2f} MXN")

    st.markdown(f"### 💡 Costo Producción Total: **${costo_produccion:.2f} MXN**")
    st.markdown(
        f"### 💰 Ganancia Neta Estimada: **${ganancia_neta:.2f} MXN**"
        f" ({markup:.0f}%)"
    )
    st.markdown(f"### 🏷️ Precio Sugerido: **${precio_final:.2f} MXN**")

    # Retornamos los datos calculados para poder usarlos al registrar la venta si se requiere
    return {
        "costo_produccion": round(costo_produccion, 2),
        "precio_final": round(precio_final, 2),
        "ganancia_neta": round(ganancia_neta, 2),
    }
  return None