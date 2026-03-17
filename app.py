
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from safety_valve import (
    SafetyValveInput,
    evaluate_safety_valve_operation,
    calculate_control_line_hydrostatic,
    calculate_required_surface_pressure,
)

st.set_page_config(
    page_title="Safety Valve Calculator",
    page_icon="🛢️",
    layout="wide"
)

st.title("🛢️ Safety Valve Calculator")
st.caption("Aplicación básica para cálculo de apertura de safety valve en completación")

st.sidebar.header("Parámetros de entrada")

tvd_ft = st.sidebar.number_input(
    "TVD de la válvula (ft)",
    min_value=0.0,
    value=8500.0,
    step=100.0
)

control_fluid_ppg = st.sidebar.number_input(
    "Densidad del fluido de control (ppg)",
    min_value=0.1,
    value=10.0,
    step=0.1
)

valve_opening_pressure_psi = st.sidebar.number_input(
    "Presión de apertura en la válvula (psi)",
    min_value=0.0,
    value=4500.0,
    step=50.0
)

friction_loss_psi = st.sidebar.number_input(
    "Pérdida por fricción en control line (psi)",
    min_value=0.0,
    value=150.0,
    step=10.0
)

available_surface_pressure_psi = st.sidebar.number_input(
    "Presión disponible en superficie (psi)",
    min_value=0.0,
    value=1000.0,
    step=50.0
)

calculate_button = st.sidebar.button("Calcular")

st.markdown("""
### Descripción
Esta app calcula:

- gradiente del fluido de control
- presión hidrostática en la control line
- presión superficial requerida para apertura
- presión efectiva en fondo
- margen operativo
- estado de la válvula
""")

if calculate_button:
    data = SafetyValveInput(
        tvd_ft=tvd_ft,
        control_fluid_ppg=control_fluid_ppg,
        valve_opening_pressure_psi=valve_opening_pressure_psi,
        available_surface_pressure_psi=available_surface_pressure_psi,
        friction_loss_psi=friction_loss_psi
    )

    results = evaluate_safety_valve_operation(data)

    if results["errors"]:
        for error in results["errors"]:
            st.error(error)
    else:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Gradiente del fluido",
                f"{results['control_fluid_gradient_psi_per_ft']:.4f} psi/ft"
            )
            st.metric(
                "Presión hidrostática",
                f"{results['hydrostatic_pressure_psi']:.2f} psi"
            )

        with col2:
            st.metric(
                "Presión superficial requerida",
                f"{results['required_surface_pressure_psi']:.2f} psi"
            )
            st.metric(
                "Presión real en fondo",
                f"{results['downhole_pressure_with_available_surface_psi']:.2f} psi"
            )

        with col3:
            st.metric(
                "Margen operativo",
                f"{results['operating_margin_psi']:.2f} psi"
            )
            st.metric(
                "Estado",
                "OPEN" if results["can_open_valve"] else "NOT OPEN"
            )

        summary_df = pd.DataFrame({
            "Parámetro": [
                "TVD de válvula",
                "Densidad fluido control",
                "Gradiente fluido",
                "Presión hidrostática",
                "Presión apertura en válvula",
                "Pérdida por fricción",
                "Presión superficial requerida",
                "Presión disponible en superficie",
                "Presión real en fondo",
                "Margen operativo",
                "¿La válvula abre?"
            ],
            "Valor": [
                f"{results['tvd_ft']:.2f} ft",
                f"{results['control_fluid_ppg']:.2f} ppg",
                f"{results['control_fluid_gradient_psi_per_ft']:.4f} psi/ft",
                f"{results['hydrostatic_pressure_psi']:.2f} psi",
                f"{results['valve_opening_pressure_required_downhole_psi']:.2f} psi",
                f"{results['friction_loss_psi']:.2f} psi",
                f"{results['required_surface_pressure_psi']:.2f} psi",
                f"{results['available_surface_pressure_psi']:.2f} psi",
                f"{results['downhole_pressure_with_available_surface_psi']:.2f} psi",
                f"{results['operating_margin_psi']:.2f} psi",
                "Sí" if results["can_open_valve"] else "No"
            ]
        })

        st.subheader("Resumen tabulado")
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

        depths = list(range(1000, 15001, 500))
        required_pressures = []

        for depth in depths:
            hydro = calculate_control_line_hydrostatic(depth, control_fluid_ppg)
            req_pressure = calculate_required_surface_pressure(
                valve_opening_pressure_psi,
                hydro,
                friction_loss_psi
            )
            required_pressures.append(req_pressure)

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(depths, required_pressures, marker="o")
        ax.set_xlabel("TVD de válvula (ft)")
        ax.set_ylabel("Presión superficial requerida (psi)")
        ax.set_title("Presión superficial requerida vs profundidad")
        ax.grid(True)

        st.subheader("Sensibilidad")
        st.pyplot(fig)

        if results["can_open_valve"]:
            st.success("La válvula sí abre con la presión disponible en superficie.")
        else:
            st.error("La válvula no abre con la presión disponible en superficie.")
