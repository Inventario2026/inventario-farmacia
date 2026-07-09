import streamlit as st
import pandas as pd
from datetime import datetime
import os
from streamlit_gsheets import GSheetsConnection

# Configuración de la página
st.set_page_config(page_title="Inventario Farmacia - Dipharma", layout="wide")

# --- CONEXIÓN DIRECTA A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_kardex_permanente():
    try:
        # Lee los datos frescos de Google sin retraso (ttl=0)
        df = conn.read(ttl="0m")
        if df.empty or "ID" not in df.columns:
            return pd.DataFrame(columns=["ID", "Fecha y Hora", "Usuario", "Acción", "Producto", "Código", "Presentación", "Marca", "Cantidad"])
        return df
    except:
        return pd.DataFrame(columns=["ID", "Fecha y Hora", "Usuario", "Acción", "Producto", "Código", "Presentación", "Marca", "Cantidad"])

def guardar_en_kardex_permanente(nuevos_registros_list):
    df_actual = cargar_kardex_permanente()
    df_nuevos = pd.DataFrame(nuevos_registros_list)
    df_final = pd.concat([df_actual, df_nuevos], ignore_index=True)
    
    # Sube y sobrescribe directamente en tu Google Sheets en tiempo real
    conn.update(data=df_final)

# Inicializar estados de la sesión
if "usuario_identificado" not in st.session_state:
    st.session_state["usuario_identificado"] = None

if "lista_espera_productos" not in st.session_state:
    st.session_state["lista_espera_productos"] = []

# --- IDENTIDAD VISUAL (FONDO) ---
def set_bg_hack(main_bg):
    st.markdown(
         f"""
         <style>
         .stApp {{
             background: url("{main_bg}");
             background-size: cover
         }}
         </style>
         """,
         unsafe_allow_html=True
     )

set_bg_hack('https://images.unsplash.com/photo-1599401764673-90d1f7c8f95c?q=80&w=2070&auto=format&fit=crop')

# PANTALLA 1: INICIO DE SESIÓN
if st.session_state["usuario_identificado"] is None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    try:
        st.image('images-removebg-preview.png', width=150)
    except:
        pass
    st.markdown("<h2 style='text-align: center; color: #1a365d;'>🔐 Acceso al Sistema de Inventario</h2>", unsafe_allow_html=True)
    st.write("---")
    
    col_izq, col_centro, col_der = st.columns([1, 1.5, 1])
    with col_centro:
        nombre_ingresado = st.text_input("👤 Ingrese su Nombre de Usuario para comenzar:")
        if st.button("🚀 Ingresar al Sistema", use_container_width=True):
            if nombre_ingresado.strip() != "":
                st.session_state["usuario_identificado"] = nombre_ingresado.strip()
                st.rerun()
            else:
                st.error("⚠️ El nombre es obligatorio.")
    st.stop()

# PANTALLA 2: SISTEMA PRINCIPAL
st.markdown("<h1 style='text-align: center; color: #1a365d;'>💊 Control de Inventario</h1>", unsafe_allow_html=True)
st.markdown(f"👤 **Usuario en línea:** {st.session_state['usuario_identificado']} | 🌐 **Base de Datos:** Nube de Google Sheets Activa")

pestana_registro, pestana_foto, pestana_kardex = st.tabs([
    "⚡ Registrar Manual", 
    "📸 Escanear Factura / Foto", 
    "🔒 Kardex Administrator"
])

# -------------------------------------------------------------------------
# PESTAÑA 1: REGISTRO MANUAL
# -------------------------------------------------------------------------
with pestana_registro:
    @st.cache_data
    def cargar_datos_excel():
        archivo = 'Libro1 (4).xlsx'
        if not os.path.exists(archivo):
            return None
        df = pd.read_excel(archivo, skiprows=3)
        df['Marca'] = df['Marca'].fillna('Sin Marca')
        df['Presemp'] = df['Presemp'].fillna('No especificada')
        return df

    df_productos = cargar_datos_excel()

    if df_productos is None:
        st.error("❌ ERROR: No se encontró el archivo 'Libro1 (4).xlsx' en esta carpeta.")
    else:
        st.markdown("### 🔍 Seleccionar Producto para la Lista")
        col1, col2 = st.columns(2)
        with col1:
            accion = st.selectbox("⚡ Tipo de Movimiento:", ["Venta / Salida", "Ingreso Factura"], key="reg_manual_accion")
            cantidad = st.number_input("🔢 Cantidad unidades:", min_value=1, step=1, key="reg_manual_cant")
        with col2:
            lista_productos = df_productos['Descripción del Producto'].dropna().unique().tolist()
            producto_seleccionado = st.selectbox("📦 Buscar Producto:", options=["-- Selecciona un medicamento --"] + lista_productos)

        if producto_seleccionado and producto_seleccionado != "-- Selecciona un medicamento --":
            datos_item = df_productos[df_productos['Descripción del Producto'] == producto_seleccionado].iloc[0]
            
            c1, c2, c3 = st.columns(3)
            c1.info(f"**Código:** {str(datos_item['Codigo'])}")
            c2.info(f"**Marca / Laboratorio:** {str(datos_item['Marca'])}")
            presentacion_final = c3.text_input("✍️ Confirmar Presentación:", value=str(datos_item['Presemp']))

            if st.button("➕ AGREGAR A LA LISTA TEMPORAL", use_container_width=True):
                nuevo_item_temporal = {
                    "Acción": accion,
                    "Producto": producto_seleccionado,
                    "Código": str(datos_item['Codigo']),
                    "Presentación": presentacion_final,
                    "Marca": str(datos_item['Marca']),
                    "Cantidad": cantidad
                }
                st.session_state["lista_espera_productos"].append(nuevo_item_temporal)
                st.success(f"¡{producto_seleccionado} agregado a la lista de abajo!")
                st.rerun()

        st.write("---")
        st.markdown("### 📋 Lista de Productos por Registrar")
        
        if len(st.session_state["lista_espera_productos"]) == 0:
            st.info("La lista está vacía. Selecciona un producto arriba.")
        else:
            df_temporal_visual = pd.DataFrame(st.session_state["lista_espera_productos"])
            st.dataframe(df_temporal_visual[["Acción", "Cantidad", "Producto", "Marca", "Presentación"]], use_container_width=True)
            
            col_izq_btn, col_der_btn = st.columns(2)
            with col_izq_btn:
                if st.button("🗑️ BORRAR TODA LA LISTA", type="secondary", use_container_width=True):
                    st.session_state["lista_espera_productos"] = []
                    st.rerun()
                    
            with col_der_btn:
                if st.button("💾 GUARDAR TODA LA LISTA COMPLETA EN EL KARDEX", type="primary", use_container_width=True):
                    ahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    
                    nuevos_registros = []
                    for item in st.session_state["lista_espera_productos"]:
                        timestamp_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
                        nuevos_registros.append({
                            "ID": str(timestamp_id),
                            "Fecha y Hora": ahora,
                            "Usuario": st.session_state['usuario_identificado'],
                            "Acción": item["Acción"],
                            "Producto": item["Producto"],
                            "Código": str(item["Código"]),
                            "Presentación": item["Presentación"],
                            "Marca": item["Marca"],
                            "Cantidad": int(item["Cantidad"])
                        })
                    
                    with st.spinner("Guardando de forma segura en Google Drive..."):
                        guardar_en_kardex_permanente(nuevos_registros)
                    st.session_state["lista_espera_productos"] = []
                    st.success("🎉 ¡Movimientos inmortalizados en Google Sheets con éxito!")
                    st.rerun()

# -------------------------------------------------------------------------
# PESTAÑA 2: FOTO / CÁMARA
# -------------------------------------------------------------------------
with pestana_foto:
    st.markdown("### 📸 Cargar ítems por Foto o Factura")
    foto_capturada = st.camera_input("Toma la foto de la factura aquí:")
    if foto_capturada is not None:
        st.success("📸 ¡Foto recibida con éxito!")
        st.image(foto_capturada, caption="Factura Cargada")

# -------------------------------------------------------------------------
# PESTAÑA 3: KARDEX ADMINISTRADOR (CONECTADO A GOOGLE SHEETS)
# -------------------------------------------------------------------------
with pestana_kardex:
    st.markdown("### 🔑 Control de Acceso")
    clave = st.text_input("Introduce la clave secreta:", type="password", key="clave_admin")
    if clave == "1999":
        st.success("🔓 Acceso Concedido - Historial Eterno de Google Drive")
        
        with st.spinner("Cargando historial desde Google Sheets..."):
            df_kardex = cargar_kardex_permanente()
        
        if df_kardex.empty:
            st.info("ℹ️ No hay registros históricos en tu Google Sheets todavía.")
        else:
            csv_completo = df_kardex.to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 EXPORTAR HISTORIAL COMPLETO DE MESES (CSV)", data=csv_completo, file_name="Historial_Kardex_Dipharma.csv", mime="text/csv", use_container_width=True)
            
            # Mostrar los registros, el más nuevo arriba
            df_mostrar = df_kardex.iloc[::-1]
                
            for idx, fila in df_mostrar.iterrows():
                with st.container():
                    col_detalles, col_boton = st.columns([6, 1])
                    with col_detalles:
                        st.markdown(f"📅 **{fila['Fecha y Hora']}** | 👤 *{fila['Usuario']}* | ⚡ {fila['Acción']} | 📦 **{fila['Producto']}** | 🏷️ Marca: {fila['Marca']} | 🔢 Cantidad: {fila['Cantidad']}")
                    with col_boton:
                        if st.button("🗑️ Eliminar", key=f"del_{fila['ID']}", type="primary"):
                            df_kardex = df_kardex[df_kardex["ID"].astype(str) != str(fila["ID"])]
                            conn.update(data=df_kardex)
                            st.rerun()
                    st.markdown("---")
    elif clave != "":
        st.error("❌ Clave incorrecta.")

st.write("---")
if st.button("🚪 Cerrar Sesión", key="btn_logout"):
    st.session_state["usuario_identificado"] = None
    st.rerun()
