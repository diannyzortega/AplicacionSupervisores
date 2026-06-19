# app.py
import os
import django
import streamlit as st
from django.apps import apps

# 1. Configuración de página (Obligatorio de primero)
st.set_page_config(
    page_title="Grupo Chargon | App Supervisores", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar Django (El check de apps.ready es instantáneo, no requiere st.cache)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_backend.settings")
if not apps.ready:
    django.setup()

from django.core.management import call_command
try:
    call_command('makemigrations', 'comercial')
    call_command('migrate')
except Exception as e:
    st.error(f"Error al aplicar migraciones de base de datos: {e}")

# =================================================================
# 🛡️ BLOQUE DE INICIALIZACIÓN ESTRICTO (Garantía Anti-Fugas de Datos)
# =================================================================
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

# Forzamos la existencia de las variables core con valores por defecto seguros.
# De esta forma, ninguna vista o barra lateral leerá datos vacíos o de sesiones previas.
if "usuario_actual" not in st.session_state:
    st.session_state["usuario_actual"] = ""

if "rol_actual" not in st.session_state:
    st.session_state["rol_actual"] = "asesor"

if "region_usuario" not in st.session_state:
    st.session_state["region_usuario"] = ""

if "sucursal_usuario" not in st.session_state:
    st.session_state["sucursal_usuario"] = ""

if "opcion_menu_actual" not in st.session_state:
    st.session_state["opcion_menu_actual"] = "📊 Dashboard General"


# Contenedor maestro anti-efecto fantasma
placeholder_pantalla = st.empty()

if not st.session_state["autenticado"]:
    with placeholder_pantalla.container():
        from src.auth.login import render_login
        render_login()
    st.stop()

else:
    # ⚡ Vaciamos de golpe el login para que libere memoria visual
    placeholder_pantalla.empty()
    
    # Renderizamos la barra lateral (Es ligera, no procesa datos pesados)
    # Ahora render_sidebar() leerá de manera segura las variables pre-inicializadas
    from src.components.sidebar import render_sidebar
    render_sidebar()
    
    # Capturamos la ruta seleccionada y limpiamos variables de rol
    menu = st.session_state.get("opcion_menu_actual", "📊 Dashboard General")
    rol_usuario = str(st.session_state.get("rol_actual", "asesor")).lower().strip()
    
    # -----------------------------------------------------------------
    # ENRUTADOR LAZY (Carga perezosa): Solo importa el archivo cuando se requiere
    # -----------------------------------------------------------------
    if menu == "📊 Dashboard General":
        with st.spinner("📊 Procesando indicadores de ventas..."):
            from src.views.dashboard import show_dashboard
            show_dashboard()
            
    elif menu == "📝 Planificación":
        with st.spinner("📝 Abriendo formulario de planificación..."):
            from src.views.planificacion import show_planificacion
            show_planificacion()
            
    elif menu == "🌙 Cierre de Resultados":
        with st.spinner("🌙 Cargando cierre..."):
            from src.views.resultados import show_resultados
            show_resultados()
            
    elif menu == "📈 Seguimiento Asesores":
        from src.views.seguimiento import show_seguimiento
        show_seguimiento()
            
    elif menu == "📅 Historial Diario":
        from src.views.historial import show_historial
        show_historial()
            
    elif menu == "👤 Vincular Asesor":
        from src.views.vincular import show_vincular
        show_vincular()
            
    elif menu == "⚙️ Configurar Empresa":
        if "admin" in rol_usuario or rol_usuario == "1":
            from src.views.configuracion import show_configuracion
            show_configuracion()
            
    elif menu == "⚙️   Configurar Categorias Foco":
        if "admin" in rol_usuario or rol_usuario == "1" or "coordinador" in rol_usuario or rol_usuario == "2":
            from src.views.categorias import show_categorias
            show_categorias()