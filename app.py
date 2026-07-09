import streamlit as st
import pandas as pd
from datetime import datetime
import os
import threading
from PIL import Image

# Configuración de la página con tema oscuro para mejor contraste
st.set_page_config(page_title="Inventario Farmacia - Dipharma", layout="wide")

# Candado de seguridad para que los datos no se crucen en internet
lock = threading.Lock()
ARCHIVO_KARDEX = "kardex_farmacia.csv"

# --- FUNCIONES DE DATOS ---
def cargar_kardex_completo():
    with lock:
        if os.path.exists(ARCHIVO_KARDEX):
            try:
                return pd.read_csv(ARCHIVO_KARDEX)
            except:
                return pd.DataFrame(columns=["ID", "Fecha y Hora", "Usuario", "Acción", "Producto", "Código", "Presentación", "Marca", "Cantidad"])
        return pd.DataFrame(columns=["ID", "Fecha y Hora", "Usuario", "Acción", "Producto", "Código", "Presentación", "Marca", "Cantidad"])

def guardar_kardex_completo(df):
    with lock:
        df.to_csv(ARCHIVO_KARDEX, index=False)

# Inicializar estados de la sesión
if "usuario_identificado" not in st.session_state:
    st.session_state["usuario_identificado"] = None

if "lista_espera_productos" not in st.session_state:
    st.session_state["lista_espera_productos"] = []

# --- AGREGAR IMÁGENES ---
def cargar_logo():
    try:
        logo = Image.open('images-removebg-preview.png')
        return logo
    except FileNotFoundError:
        return None

logo_dipharma = cargar_logo()

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
    if logo_dipharma:
        st.image(logo_dipharma, width=150, clamp=True)
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
st.markdown(f"👤 **Usuario en línea:** {st.session_state['usuario_identificado']}")

pestana_registro, pestana_foto, pestana_kardex = st.tabs([
    "⚡ Registrar Manual", 
    "📸 Escanear Factura / Foto", 
    "🔒 Kardex Administrador"
])

# -------------------------------------------------------------------------
# PESTAÑA 1: REGISTRO MANUAL (AHORA CON LISTA DE ESPERA MULTI-PRODUCTO)
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
        # Formulario superior para seleccionar UN producto
        st.markdown("### 🔍 Seleccionar Producto para la Lista")
        col1, col2 = st.columns(2)
        with col1:
            accion = st.selectbox("⚡ Tipo de Movimiento:", ["Venta / Salida", "Ingreso Factura"], key="reg_manual_accion")
            cantidad = st.number_input("🔢 Cantidad unidades:", min_value=1, step=1, key="reg_manual_cant")
        with col2:
            lista_productos = df_productos['Descripción del Producto'].dropna().unique().tolist()
            producto_seleccionado = st.selectbox("📦 Buscar Producto:", options=["-- Selecciona un medicamento --"] + lista_productos)

        # Si hay un producto seleccionado válido, mostrar sus datos y el botón de agregar
        if producto_seleccionado and producto_seleccionado != "-- Selecciona un medicamento --":
            datos_item = df_productos[df_productos['Descripción del Producto'] == producto_seleccionado].iloc[0]
            
            c1, c2, c3 = st.columns(3)
            c1.info(f"**Código:** {str(datos_item['Codigo'])}")
            c2.info(f"**Marca / Laboratorio:** {str(datos_item['Marca'])}")
            presentacion_final = c3.text_input("✍️ Confirmar Presentación:", value=str(datos_item['Presemp']))

            # Botón para añadir este artículo específico a la cola temporal
            if st.button("➕ AGREGAR A LA LISTA TEMPORAL", use_container_width=True):
                nuevo_item_temporal = {
                    "Acción": accion,
                    "Producto": producto_seleccionado,
                    "Código": str(datos_item['Codigo']),
                    "Presentación": presentacion_final,
                    "Marca": str(datos_item['Marca']),
                    "Cantidad": cantidad
                }
                # Lo metemos en nuestra lista de la sesión
                st.session_state["lista_espera_productos"].append(nuevo_item_temporal)
                st.success(f"¡{producto_seleccionado} agregado a la lista de abajo!")
                st.rerun()

        # Visualización de la Lista de Espera actual
        st.write("---")
        st.markdown("### 📋 Lista de Productos por Registrar")
        
        if len(st.session_state["lista_espera_productos"]) == 0:
            st.info("La lista está vacía. Selecciona un producto arriba y haz clic en 'Agregar a la lista temporal'.")
        else:
            # Mostrar los productos agregados uno abajo del otro tipo tabla
            df_temporal_visual = pd.DataFrame(st.session_state["lista_espera_productos"])
            st.dataframe(df_temporal_visual[["Acción", "Cantidad", "Producto", "Marca", "Presentación"]], use_container_width=True)
            
            col_izq_btn, col_der_btn = st.columns(2)
            with col_izq_btn:
                if st.button("🗑️ BORRAR TODA LA LISTA", type="secondary", use_container_width=True):
                    st.session_state["lista_espera_productos"] = []
                    st.toast("Lista limpiada")
                    st.rerun()
                    
            with col_der_btn:
                # El botón definitivo que guarda todo el bloque en el Kardex verdadero
                if st.button("💾 GUARDAR TODA LA LISTA COMPLETA EN EL KARDEX", type="primary", use_container_width=True):
                    ahora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    df_kardex_actual = cargar_kardex_completo()
                    
                    nuevos_registros = []
                    for item in st.session_state["lista_espera_productos"]:
                        timestamp_id = datetime.now().strftime("%Y%m%d%H%M%S%f") + str(os.urandom(2).hex())
                        nuevos_registros.append({
                            "ID": timestamp_id,
                            "Fecha y Hora": ahora,
                            "Usuario": st.session_state['usuario_identificado'],
                            "Acción": item["Acción"],
                            "Producto": item["Producto"],
                            "Código": item["Código"],
                            "Presentación": item["Presentación"],
                            "Marca": item["Marca"],
                            "Cantidad": item["Cantidad"]
                        })
                    
                    df_nuevos = pd.DataFrame(nuevos_registros)
                    df_kardex_actual = pd.concat([df_kardex_actual, df_nuevos], ignore_index=True)
                    guardar_kardex_completo(df_kardex_actual)
                    
                    # Limpiamos la lista temporal una vez guardado
                    st.session_state["lista_espera_productos"] = []
                    st.success("🎉 ¡Todos los productos de la lista se han guardado con éxito en el Kardex!")
                    st.rerun()

# -------------------------------------------------------------------------
# PESTAÑA 2: FOTO / CÁMARA
# -------------------------------------------------------------------------
with pestana_foto:
    st.markdown("### 📸 Cargar ítems por Foto o Factura")
    st.info("Usa esta opción si estás en tu celular para activar la cámara trasera o sube una foto.")
    
    foto_capturada = st.camera_input("Toma la foto de la factura o el producto aquí:")
    if foto_capturada is not None:
        st.success("📸 ¡Foto recibida con éxito!")
        st.image(foto_capturada, caption="Factura / Ítem Cargado")
        st.warning("🤖 [Nota de Desarrollo]: La foto se guardó temporalmente. Para que la IA lea el texto exacto automáticamente, en el siguiente paso la conectaremos con el lector óptico.")

# -------------------------------------------------------------------------
# PESTAÑA 3: KARDEX ADMINISTRADOR
# -------------------------------------------------------------------------
with pestana_kardex:
    st.markdown("### 🔑 Control de Acceso")
    clave = st.text_input("Introduce la clave secreta:", type="password", key="clave_admin")
    if clave == "1999":
        st.success("🔓 Acceso Concedido")
        df_kardex = cargar_kardex_completo()
        if df_kardex.empty:
            st.info("ℹ️ El Kardex está vacío.")
        else:
            csv_completo = df_kardex.drop(columns=["ID"]).to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 EXPORTAR TODO EL KARDEX", data=csv_completo, file_name="Kardex.csv", mime="text/csv", use_container_width=True)
            
            for idx, fila in df_kardex.iterrows():
                with st.container():
                    col_detalles, col_boton = st.columns([6, 1])
                    with col_detalles:
                        st.markdown(f"📅 **{fila['Fecha y Hora']}** | 👤 *{fila['Usuario']}* | ⚡ {fila['Acción']} | 📦 **{fila['Producto']}** | 🏷️ Marca: {fila['Marca']} | 🔢 Cantidad: {fila['Cantidad']}")
                    with col_boton:
                        if st.button("🗑️ Eliminar", key=f"del_{fila['ID']}", type="primary"):
                            df_kardex = df_kardex[df_kardex["ID"] != fila["ID"]]
                            guardar_kardex_completo(df_kardex)
                            st.rerun()
    elif clave != "":
        st.error("❌ Clave incorrecta.")

st.write("---")
if st.button("🚪 Cerrar Sesión", key="btn_logout"):
    st.session_state["usuario_identificado"] = None
    st.rerun()