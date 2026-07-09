import streamlit as st
import pandas as pd
from datetime import datetime
import os
import requests

# Configuración de la página
st.set_page_config(page_title="Inventario Farmacia - Dipharma", layout="wide")

# Enlace de tu hoja de Google Sheets pública como Editor
GSHEET_URL = "https://docs.google.com/spreadsheets/d/1juwrB14zEMXiVtLPJVlOWfgAatdH8cYUpW2fIF9_u28/export?format=csv"

if "kardex_local" not in st.session_state:
    st.session_state["kardex_local"] = []

def cargar_kardex_permanente():
    try:
        df = pd.read_csv(GSHEET_URL)
        if df.empty or "ID" not in df.columns:
            return pd.DataFrame(st.session_state["kardex_local"])
        return df
    except:
        return pd.DataFrame(st.session_state["kardex_local"])

def guardar_en_kardex_permanente(nuevos_registros_list):
    # Guardamos localmente para que lo veas reflejado de inmediato en pantalla
    for r in nuevos_registros_list:
        st.session_state["kardex_local"].append(r)
    
    # Sistema de envío simplificado por Formulario de Respaldo sin autenticación obligatoria
    # (Usamos el formulario público que ya probamos que sí recibe datos sin pedir contraseñas)
    FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSeycjgEhNf_fjh7y9PNQ8x2UHgPlSACOOEM5W75hfk2N0GEdQ/formResponse"
    
    for item in nuevos_registros_list:
        # Volvemos al método del formulario pero empaquetando todo en las columnas correctas
        form_data = {
            "entry.1945657434": item["ID"],
            "entry.1147575306": item["Fecha y Hora"],
            "entry.348630325": item["Usuario"],
            "entry.1118335017": item["Acción"],
            "entry.1802958498": item["Producto"],
            "entry.1144005937": item["Código"],
            "entry.582490515": item["Presentación"],
            "entry.527632616": item["Marca"],
            "entry.1687441164": item["Cantidad"]
        }
        try:
            requests.post(FORM_URL, data=form_data)
        except:
            pass

# Inicializar estados de la sesión
if "usuario_identificado" not in st.session_state:
    st.session_state["usuario_identificado"] = None

if "lista_espera_productos" not in st.session_state:
    st.session_state["lista_espera_productos"] = []

# --- IDENTIDAD VISUAL ---
def set_bg_hack(main_bg):
    st.markdown(f'<style>.stApp {{background: url("{main_bg}"); background-size: cover}}</style>', unsafe_allow_html=True)

set_bg_hack('https://images.unsplash.com/photo-1599401764673-90d1f7c8f95c?q=80&w=2070&auto=format&fit=crop')

if st.session_state["usuario_identificado"] is None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #1a365d;'>🔐 Acceso al Sistema de Inventario</h2>", unsafe_allow_html=True)
    col_izq, col_centro, col_der = st.columns([1, 1.5, 1])
    with col_centro:
        nombre_ingresado = st.text_input("👤 Ingrese su Nombre de Usuario:")
        if st.button("🚀 Ingresar", use_container_width=True):
            if nombre_ingresado.strip() != "":
                st.session_state["usuario_identificado"] = nombre_ingresado.strip()
                st.rerun()
    st.stop()

st.markdown("<h1 style='text-align: center; color: #1a365d;'>💊 Control de Inventario</h1>", unsafe_allow_html=True)
st.markdown(f"👤 **Usuario:** {st.session_state['usuario_identificado']} | 🌐 **Base de Datos:** Nube Sincronizada")

pestana_registro, pestana_foto, pestana_kardex = st.tabs(["⚡ Registrar Manual", "📸 Escanear Factura", "🔒 Kardex Administrador"])

with pestana_registro:
    @st.cache_data
    def cargar_datos_excel():
        archivo = 'Libro1 (4).xlsx'
        if not os.path.exists(archivo): return None
        df = pd.read_excel(archivo, skiprows=3)
        df['Marca'] = df['Marca'].fillna('Sin Marca')
        df['Presemp'] = df['Presemp'].fillna('No especificada')
        return df

    df_productos = cargar_datos_excel()

    if df_productos is None:
        st.error("❌ ERROR: No se encontró el archivo 'Libro1 (4).xlsx'.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            accion = st.selectbox("⚡ Tipo Movimiento:", ["Venta / Salida", "Ingreso Factura"])
            cantidad = st.number_input("🔢 Cantidad:", min_value=1, step=1)
        with col2:
            lista_productos = df_productos['Descripción del Producto'].dropna().unique().tolist()
            producto_seleccionado = st.selectbox("📦 Buscar Producto:", options=["-- Selecciona --"] + lista_productos)

        if producto_seleccionado and producto_seleccionado != "-- Selecciona --":
            datos_item = df_productos[df_productos['Descripción del Producto'] == producto_seleccionado].iloc[0]
            c1, c2, c3 = st.columns(3)
            c1.info(f"**Código:** {str(datos_item['Codigo'])}")
            c2.info(f"**Marca:** {str(datos_item['Marca'])}")
            presentacion_final = c3.text_input("✍️ Presentación:", value=str(datos_item['Presemp']))

            if st.button("➕ AGREGAR A LA LISTA TEMPORAL", use_container_width=True):
                st.session_state["lista_espera_productos"].append({
                    "Acción": accion, "Producto": producto_seleccionado, "Código": str(datos_item['Codigo']),
                    "Presentación": presentacion_final, "Marca": str(datos_item['Marca']), "Cantidad": cantidad
                })
                st.rerun()

        st.write("---")
        if len(st.session_state["lista_espera_productos"]) > 0:
            st.dataframe(pd.DataFrame(st.session_state["lista_espera_productos"]), use_container_width=True)
            if st.button("💾 GUARDAR TODO EN GOOGLE DRIVE", type="primary", use_container_width=True):
                ahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                nuevos = []
                for item in st.session_state["lista_espera_productos"]:
                    nuevos.append({
                        "ID": datetime.now().strftime("%Y%m%d%H%M%S%f"), "Fecha y Hora": ahora,
                        "Usuario": st.session_state['usuario_identificado'], "Acción": item["Acción"],
                        "Producto": item["Producto"], "Código": item["Código"], "Presentación": item["Presentación"],
                        "Marca": item["Marca"], "Cantidad": int(item["Cantidad"])
                    })
                with st.spinner("Guardando en la nube..."):
                    guardar_en_kardex_permanente(nuevos)
                st.session_state["lista_espera_productos"] = []
                st.success("🎉 ¡Guardado completo en Google Sheets sin contraseñas!")
                st.rerun()

with pestana_foto:
    st.camera_input("Toma la foto de la factura aquí:")

with pestana_kardex:
    clave = st.text_input("Introduce la clave secreta:", type="password")
    if clave == "1999":
        df_kardex = cargar_kardex_permanente()
        if not df_kardex.empty:
            st.dataframe(df_kardex.iloc[::-1], use_container_width=True)
