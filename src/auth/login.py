# src/auth/login.py
import streamlit as st
import time
import os
import base64
from django.contrib.auth import authenticate
from comercial.models import Region, Sucursal

def render_login():
    # 1. Centrar el contenedor del login usando las columnas
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        # Metemos todo dentro del contenedor con borde para darle estructura de tarjeta
        with st.container(border=True):
            
            # --- Lógica de procesamiento y renderizado del Logo ---
            ruta_logo = "assets/Grupo Chargon (LOGO BLANCO).png"
            img_html = ""
            
            if os.path.exists(ruta_logo):
                try:
                    with open(ruta_logo, "rb") as image_file:
                        encoded_string = base64.b64encode(image_file.read()).decode()
                    # Agregamos "display: block; margin: 0 auto;" para forzar el centrado del logo en la tarjeta
                    img_html = f'<div style="text-align: center;"><img src="data:image/png;base64,{encoded_string}" style="width: 150px; margin-bottom: 15px;"></div>'
                except Exception:
                    img_html = "<div style='text-align: center; font-size: 50px; margin-bottom: 15px;'>🏢</div>"
            else:
                img_html = "<div style='text-align: center; font-size: 50px; margin-bottom: 15px;'>🏢</div>"
            
            # ¡CRUCIAL! Renderizamos el HTML generado para que el logo se vea en pantalla
            st.markdown(img_html, unsafe_allow_html=True)
            
            # --- Formulario de Entrada ---
            with st.form("login_form", clear_on_submit=False):
                st.markdown("<h4 style='text-align: center; color: white; margin-top: 0;'>Iniciar Sesión</h4>", unsafe_allow_html=True)
                usuario_input = st.text_input("👤 Usuario", placeholder="Ingresa tu usuario...")
                clave_input = st.text_input("🔑 Contraseña", type="password", placeholder="Ingresa tu contraseña...")
                
                submit = st.form_submit_button("🚀 Ingresar al Sistema", use_container_width=True)
                
                if submit:
                    if not usuario_input or not clave_input:
                        st.error("⚠️ Por favor, completa todos los campos.")
                    else:
                        with st.spinner("Verificando credenciales..."):
                            try:
                                user = authenticate(username=usuario_input.strip(), password=clave_input.strip())
                                
                                if user is not None:
                                    # Obtener el perfil
                                    try:
                                        profile = user.profile
                                        
                                        # Guardamos las variables de control en el estado de sesión
                                        st.session_state["autenticado"] = True
                                        st.session_state["usuario_actual"] = profile.nombre
                                        st.session_state["id_usuario_actual"] = profile.id_usuario
                                        st.session_state["rol_actual"] = str(profile.id_rol).lower().strip()
                                        
                                        # Buscar nombres de región y sucursal
                                        try:
                                            region_obj = Region.objects.get(id_region=profile.id_region)
                                            st.session_state["region_usuario"] = region_obj.nombre_region
                                        except Region.DoesNotExist:
                                            st.session_state["region_usuario"] = ""
                                            
                                        try:
                                            sucursal_obj = Sucursal.objects.get(id_sucursal=profile.id_sucursal)
                                            st.session_state["sucursal_usuario"] = sucursal_obj.nombre_sucursal
                                        except Sucursal.DoesNotExist:
                                            st.session_state["sucursal_usuario"] = ""
                                        
                                        st.session_state["opcion_menu_actual"] = "📊 Dashboard General"
                                        
                                        st.toast(f"¡Bienvenido, {profile.nombre}! 👋", icon="✅")
                                        time.sleep(0.5)
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error cargando el perfil del usuario: {e}")
                                else:
                                    st.error("❌ Usuario o contraseña incorrectos. Revisa e intenta de nuevo.")
                            except Exception as e:
                                st.error(f"Error de autenticación con Django: {e}")