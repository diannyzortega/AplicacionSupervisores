# src/components/sidebar.py
import streamlit as st
import os
import base64

# Ruta exacta indicada para almacenar los perfiles
FOTOS_DIR = "data/fotos_perfil"

# Nos aseguramos de que la carpeta exista para evitar errores
if not os.path.exists(FOTOS_DIR):
    os.makedirs(FOTOS_DIR)

@st.cache_data(ttl=3600, show_spinner=False)
def obtener_avatar_base64(ruta_foto, mod_time):
    """Lee y codifica la imagen. Se recarga solo si cambia la fecha de modificación."""
    with open(ruta_foto, "rb") as f:
        return base64.b64encode(f.read()).decode()

def render_sidebar():
    # Obtenemos el rol y lo limpiamos de decimales molestos (.0) si vienen como flotantes
    rol_raw = str(st.session_state.get("rol_actual", "asesor")).replace(".0", "").strip().lower()
    nombre_usuario = st.session_state.get('usuario_actual', 'Usuario')
    id_user = str(st.session_state.get('id_usuario_actual', '0')).replace(".0", "").strip()
    
    st.sidebar.markdown('<h4 style="color: #4A90E2; margin-bottom: 15px; text-align: center;">Perfil Activo</h4>', unsafe_allow_html=True)
    
    # --- 1. Lógica de renderizado del avatar circular ---
    ruta_foto = os.path.join(FOTOS_DIR, f"user_{id_user}.png")
    if os.path.exists(ruta_foto):
        try:
            mod_time = os.path.getmtime(ruta_foto)
            data_foto = obtener_avatar_base64(ruta_foto, mod_time)
            html_avatar = f'<div style="text-align:center; margin-bottom: 15px;"><img src="data:image/png;base64,{data_foto}" style="width:90px; height:90px; border-radius:50%; object-fit: cover; border: 2px solid #4A90E2;"></div>'
        except Exception:
            iniciales = "".join([part[0].upper() for part in nombre_usuario.split()[:2]])
            html_avatar = f'<div style="display: flex; align-items: center; justify-content: center; margin: 0 auto 15px auto; background:#2E4053; color:white; width:90px; height:90px; border-radius:50%; font-size: 28px; font-weight: bold; border: 2px solid #4A90E2;">{iniciales}</div>'
    else:
        iniciales = "".join([part[0].upper() for part in nombre_usuario.split()[:2]])
        html_avatar = f'<div style="display: flex; align-items: center; justify-content: center; margin: 0 auto 15px auto; background:#2E4053; color:white; width:90px; height:90px; border-radius:50%; font-size: 28px; font-weight: bold; border: 2px solid #4A90E2;">{iniciales}</div>'
        
    st.sidebar.markdown(html_avatar, unsafe_allow_html=True)
    
    # --- 2. MAPEO SEGURO DE ROLES ---
    mapeo_roles = {
        "1": "ADMINISTRADOR",
        "administrador": "ADMINISTRADOR",
        "2": "COORDINADOR ANDES",
        "coordinador": "COORDINADOR ANDES",
        "3": "SUPERVISOR VENTAS",
        "supervisor": "SUPERVISOR VENTAS"
    }
    
    rol_formateado = mapeo_roles.get(
        rol_raw, 
        rol_raw.replace("_", " ").upper().replace("SUP ", "SUPERVISOR ").replace("COORD ", "COORDINADOR ")
    )
        
    st.sidebar.write(f"👤 **Usuario:** {nombre_usuario}")
    st.sidebar.write(f"💼 **Rol:** {rol_formateado}")
    
    # --- 3. BOTÓN PARA SUBIR FOTO DE PERFIL (Formulario aislado) ---
    with st.sidebar.expander("📸 Cambiar foto de perfil"):
        with st.form("form_foto", clear_on_submit=True):
            foto_subida = st.file_uploader("Subir imagen (PNG/JPG)", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
            btn_guardar_foto = st.form_submit_button("Guardar Foto", use_container_width=True)
            
            if btn_guardar_foto and foto_subida is not None:
                try:
                    from PIL import Image
                    
                    nueva_ruta = os.path.join(FOTOS_DIR, f"user_{id_user}.png")
                    
                    # Abrimos la imagen con Pillow
                    img = Image.open(foto_subida)
                    
                    # Convertimos a RGB si tiene transparencia (RGBA) para evitar problemas, aunque guardaremos como PNG
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGBA")
                        
                    # Redimensionar la imagen a un tamaño óptimo para avatares (200x200)
                    img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                    
                    # Guardar la imagen optimizada (sobreescribiendo si existe)
                    img.save(nueva_ruta, format="PNG", optimize=True)
                    
                    st.success("¡Foto actualizada y optimizada!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al optimizar y guardar: {e}")
    
    st.sidebar.write("---")
    st.sidebar.markdown("<h4 style='color: #4A90E2; margin-bottom: 10px;'>MENÚ</h4>", unsafe_allow_html=True)
    
    # --- 4. CONTROL DE OPCIONES DEL MENÚ (Sincronizado con app.py) ---
    # Centralizamos las opciones para evitar inconsistencias de texto
    if "administrador" in rol_raw or rol_raw == "1":
        opciones_menu = [
            "📊 Dashboard General", 
            "📝 Planificación", 
            "🌙 Cierre de Resultados", 
            "📈 Seguimiento Asesores",
            "📅 Historial Diario",
            "⚙️ Configurar Empresa",
            "⚙️   Configurar Categorias Foco"
        ]
    elif "supervisor" in rol_raw or rol_raw == "3":
        opciones_menu = [
            "📊 Dashboard General", 
            "📝 Planificación", 
            "🌙 Cierre de Resultados",
            "📈 Seguimiento Asesores",
            "📅 Historial Diario",
            "👤 Vincular Asesor"
        ]
    else:
        # Coordinadores u otros roles de consulta
        opciones_menu = [
            "📊 Dashboard General", 
            "📝 Planificación",  
            "🌙 Cierre de Resultados",
            "📈 Seguimiento Asesores", 
            "📅 Historial Diario",
            "⚙️   Configurar Categorias Foco"
        ]
        
    if "opcion_menu_actual" not in st.session_state or st.session_state["opcion_menu_actual"] not in opciones_menu:
        st.session_state["opcion_menu_actual"] = opciones_menu[0]
        
    def cambiar_menu(opcion_seleccionada):
        st.session_state["opcion_menu_actual"] = opcion_seleccionada

    for opcion in opciones_menu:
        # Resaltamos visualmente cuál pestaña tiene activa el usuario
        es_activa = st.session_state.get("opcion_menu_actual") == opcion
        tipo_boton = "primary" if es_activa else "secondary"
        
        st.sidebar.button(
            opcion, 
            key=f"btn_{opcion}", 
            use_container_width=True, 
            type=tipo_boton,
            on_click=cambiar_menu,
            args=(opcion,)
        )
            
    st.sidebar.write("---")
    st.sidebar.markdown("<b style='color:#8a99ad;'>SOPORTE</b>", unsafe_allow_html=True)
    
    if st.sidebar.button("🔄 Sincronizar Base de Datos", use_container_width=True):
        st.cache_data.clear()
        st.toast("Base de datos sincronizada", icon="⚡")
        st.rerun()
            
    st.sidebar.write("---")
    
    def cerrar_sesion():
        st.session_state["autenticado"] = False
        st.session_state.clear()
        
    st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True, on_click=cerrar_sesion)