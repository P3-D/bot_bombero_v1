import streamlit as st
import pandas as pd
# Importarías tu conexión a base_datos.py aquí

def main():
    st.set_page_config(page_title="Dashboard Bomberos", page_icon="🚒")
    
    st.title("🚒 Estadísticas de Emergencias")
    st.sidebar.header("Filtros")
    
    # Simulación de datos (Esto vendría de tu emergencias.db)
    data = {
        'Fecha': ['2026-04-01', '2026-04-02', '2026-04-03'],
        'Tipo': ['Incendio', 'Rescate', 'Hazmat'],
        'Unidad': ['B-1', 'R-1', 'H-1']
    }
    df = pd.DataFrame(data)
    
    st.metric("Total Emergencias Abril", len(df))
    
    st.subheader("Últimas Salidas")
    st.table(df)
    
    st.subheader("Distribución por Tipo")
    st.bar_chart(df['Tipo'].value_counts())

if __name__ == "__main__":
    main()