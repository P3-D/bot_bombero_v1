import streamlit as st
import pandas as pd
from src.config import Config

# 🔌 Usamos nuestra conexión centralizada para no romper la arquitectura
from src.core.database import obtener_conexion

# 1. Configuración de la fachada
st.set_page_config(
    page_title="HUD Comandancia | Bomberos",
    page_icon="🚒",
    layout="wide"
)

# ==========================================
# 🔐 SISTEMA DE SEGURIDAD BÁSICO
# ==========================================
def check_password():
    """Retorna True si el usuario ingresó la contraseña correcta."""
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False

    if not st.session_state["autenticado"]:
        st.warning("🔒 Área Restringida. Ingrese credenciales de Oficial de Guardia.")
        # Por ahora usamos '132' como clave de prototipo. 
        # A futuro lo ideal es ponerla en tu archivo .env
        clave = st.text_input("Contraseña Operativa", type="password")
        if st.button("Ingresar"):
            if clave == "132":
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta.")
        return False
    return True

# Si no pasa la seguridad, se detiene aquí
if not check_password():
    st.stop()

# ==========================================
# ⚙️ MOTOR DE DATOS
# ==========================================
@st.cache_data(ttl=60) # Refresca los datos cada 60 segundos
def cargar_datos(tabla):
    """Lee datos desde SQLite usando la conexión oficial."""
    try:
        # ¡Magia V2.0! Abrimos con la llave maestra de tu core
        with obtener_conexion() as conn:
            query = f"SELECT * FROM {tabla} ORDER BY id DESC"
            df = pd.read_sql_query(query, conn)
            return df
    except Exception as e:
        st.error(f"Error al leer tabla {tabla}: {e}")
        return pd.DataFrame()

# Extraemos ambas tablas (Partes y Sugerencias)
df_partes = cargar_datos("partes")
df_sugerencias = cargar_datos("sugerencias")

# ==========================================
# 📊 CONSTRUCCIÓN VISUAL DEL DASHBOARD
# ==========================================
st.title("🚒 HUD Comandancia - Visor Térmico")
st.markdown("Panel de control en tiempo real del Sistema de Gestión de Emergencias.")

if df_partes.empty:
    st.info("🟢 El sistema está en línea. Esperando la primera alarma...")
else:
    # 📑 CREAMOS DOS PESTAÑAS (Para no amontonar todo)
    tab1, tab2 = st.tabs(["📊 Operaciones", "💡 Sugerencias y Feedback"])

    # --- PESTAÑA 1: OPERACIONES ---
    with tab1:
        # A. LOS KPIs (Indicadores Clave)
        st.subheader("Resumen Operativo")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Emergencias", len(df_partes))
        with col2:
            km_totales = df_partes['km_recorridos'].sum()
            st.metric("KM Totales Recorridos", f"{km_totales} km")
        with col3:
            unidades = df_partes['unidad'].nunique()
            st.metric("Unidades Desplegadas", unidades)
        with col4:
            # Protegemos el conteo por si alguien escribe la clave en minúscula
            rescates = len(df_partes[df_partes['clave'].str.upper() == '10-4'])
            st.metric("Rescates Vehiculares (10-4)", rescates)

        st.divider()

        # B. GRÁFICOS (Lo que le faltaba a tu versión)
        st.subheader("Análisis Estadístico")
        grafico_col1, grafico_col2 = st.columns(2)
        
        with grafico_col1:
            st.markdown("**Emergencias por Clave**")
            # Cuenta cuántas veces se repite cada clave y lo grafica
            st.bar_chart(df_partes['clave'].value_counts())
            
        with grafico_col2:
            st.markdown("**Salidas por Unidad**")
            st.bar_chart(df_partes['unidad'].value_counts())

        st.divider()

        # C. TABLA MAESTRA (Filtro y búsqueda integrada)
        st.subheader("📋 Libro de Guardia Histórico")
        unidades_disponibles = ["Todas"] + list(df_partes['unidad'].unique())
        filtro_unidad = st.selectbox("Filtrar por Unidad:", unidades_disponibles)
        
        if filtro_unidad != "Todas":
            df_mostrar = df_partes[df_partes['unidad'] == filtro_unidad]
        else:
            df_mostrar = df_partes

        st.dataframe(df_mostrar, use_container_width=True, hide_index=True)

    # --- PESTAÑA 2: SUGERENCIAS ---
    with tab2:
        st.subheader("Buzón de Voluntarios")
        if df_sugerencias.empty:
            st.info("No hay sugerencias registradas todavía.")
        else:
            st.dataframe(df_sugerencias, use_container_width=True, hide_index=True)