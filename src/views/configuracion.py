# src/views/configuracion.py
import streamlit as st
import pandas as pd
import plotly.express as px
from src.database.queries import cargar_tabla_cached, actualizar_tabla_excel

def show_configuracion():
    st.title("⚙️ Control de Estructura Comercial")
    st.markdown("<p style='color: #A0AAB2;'></p>", unsafe_allow_html=True)
    st.write("---")

    # Cargar tablas de base de datos
    tb_sucursales = cargar_tabla_cached("T_Sucursales")
    tb_regiones = cargar_tabla_cached("T_Regiones")
    tb_usuarios = cargar_tabla_cached("T_Usuarios")
    tb_rol = cargar_tabla_cached("T_Rol")
    tb_asesores = cargar_tabla_cached("T_Asesores")
    tb_categorias = cargar_tabla_cached("T_Categorias")
    
    # Crear tb_sucursales_completa combinando sucursales y regiones
    if not tb_sucursales.empty and not tb_regiones.empty:
        tb_sucursales_completa = tb_sucursales.merge(tb_regiones, on="ID_Region", how="left")
    else:
        tb_sucursales_completa = tb_sucursales.copy()

    # =========================================================
    # SECCIÓN: "MENU DE CONFIGURACION DE ADMIN"
    # =========================================================
    # 1. CONTROL DE NAVEGACIÓN Y MENSAJES ENTRE RERUNS
    if "pestaña_activa" not in st.session_state:
        st.session_state["pestaña_activa"] = 0
    if "mensaje_exito" not in st.session_state:
        st.session_state["mensaje_exito"] = None

    # Guardar temporalmente el mensaje para renderizarlo localmente en la pestaña correcta
    mensaje_local = st.session_state.get("mensaje_exito")
    pestaña_activa_local = st.session_state.get("pestaña_activa", 0)

    # Inicializamos las pestañas
    pestana_config = st.tabs(
        ["🏢 Estructura Geográfica", "👤 Alta de Supervisores", "🏃 Alta de Personal y Categorías", "🔍 Visor y Edición de Datos"]
    )
    
    # ==========================================
    # PESTAÑA 0: SUCURSALES
    # ==========================================
    with pestana_config[0]:
        st.subheader("Registrar Nueva Sucursal")
        siguiente_id_sucursal = int(tb_sucursales["ID_Sucursal"].max() + 1) if not tb_sucursales.empty else 101
        
        with st.form("F_Suc", clear_on_submit=True):
            nom_s = st.text_input("Nombre Sucursal:")
            r_padre = st.selectbox("Región destino:", tb_regiones["Nombre_Region"].tolist() if not tb_regiones.empty else [])
            
            if st.form_submit_button("Guardar Sucursal"):
                if nom_s.strip() == "": 
                    st.error("❌ El nombre de la sucursal no puede estar vacío.")
                else:
                    id_r_sel = tb_regiones[tb_regiones["Nombre_Region"] == r_padre].iloc[0]["ID_Region"]
                    nueva_suc_df = pd.DataFrame([{"ID_Sucursal": siguiente_id_sucursal, "Nombre_Sucursal": nom_s.strip(), "ID_Region": id_r_sel}])
                    
                    # Guardamos estados antes de actualizar (actualizar_tabla_excel hace rerun)
                    msg = f"🏢 ¡Excelente! Sucursal '{nom_s.strip()}' registrada correctamente."
                    st.session_state["mensaje_exito"] = msg
                    st.session_state["pestaña_activa"] = 0
                    st.toast(msg, icon="🏢")
                    actualizar_tabla_excel(pd.concat([tb_sucursales, nueva_suc_df], ignore_index=True), "T_Sucursales")
                    
        if mensaje_local and pestaña_activa_local == 0:
            st.success(mensaje_local)
            st.session_state["mensaje_exito"] = None

                    
    # ==========================================
    # PESTAÑA 1: SUPERVISORES
    # ==========================================
    with pestana_config[1]:
        st.subheader("Crear Cuenta para Coordinador o Supervisor")
        with st.form("Form_Sup", clear_on_submit=True):
            nombre_real = st.text_input("Nombre Completo:")
            username = st.text_input("Usuario:")
            password = st.text_input("Contraseña:", type="password")
            tipo_p = st.selectbox("Cargo:", ["Coordinador Regional", "Supervisor de Sucursal"])
            reg_asig = st.selectbox("Región Asignada:", tb_regiones["Nombre_Region"].tolist() if not tb_regiones.empty else [])
            suc_asig = st.selectbox("Sucursal Asignada (Solo Supervisores):", tb_sucursales_completa["Nombre_Sucursal"].tolist() if not tb_sucursales_completa.empty else [])
            
            if st.form_submit_button("Registrar Usuario"):
                id_r_sel = tb_regiones[tb_regiones["Nombre_Region"] == reg_asig].iloc[0]["ID_Region"]
                id_s_sel = tb_sucursales_completa[tb_sucursales_completa["Nombre_Sucursal"] == suc_asig].iloc[0]["ID_Sucursal"] if tipo_p == "Supervisor de Sucursal" else 0
                id_rol_sel = 3 if tipo_p == "Supervisor de Sucursal" else 2
                nuevo_id = int(tb_usuarios["ID_Usuario"].max() + 1) if not tb_usuarios.empty else 1
                nuevo_u = pd.DataFrame([{"ID_Usuario": nuevo_id, "Nombre": nombre_real, "User": username, "Clave": password, "ID_Rol": id_rol_sel, "ID_Region": id_r_sel, "ID_Sucursal": id_s_sel}])
                
                # Guardamos estados antes de actualizar (actualizar_tabla_excel hace rerun)
                msg = f"👤 ¡Usuario '{username}' creado con éxito!"
                st.session_state["mensaje_exito"] = msg
                st.session_state["pestaña_activa"] = 1
                st.toast(msg, icon="👤")
                actualizar_tabla_excel(pd.concat([tb_usuarios, nuevo_u], ignore_index=True), "T_Usuarios")
                
        if mensaje_local and pestaña_activa_local == 1:
            st.success(mensaje_local)
            st.session_state["mensaje_exito"] = None

                
    # ==========================================
    # PESTAÑA 2: ALTA DE PERSONAL
    # ==========================================
    with pestana_config[2]:
        st.subheader("🏃 Vincular Asesor Comercial")
        tb_sups = tb_usuarios[tb_usuarios["ID_Rol"] == 3].copy()
        if not tb_sups.empty and not tb_sucursales_completa.empty:
            tb_sups = tb_sups.merge(tb_sucursales_completa, on="ID_Sucursal", how="left")
            tb_sups["Visualizacion"] = tb_sups["Nombre"] + " (" + tb_sups["Nombre_Sucursal"].fillna("Sin Sucursal") + ")"
            
            with st.form("Form_Asesores", clear_on_submit=True):
                id_asesor_nuevo = st.text_input("Código de Ruta / ID Asesor:", placeholder="Ej: R011, M005, 101").strip().upper()
                nom_asesor = st.text_input("Nombre del Asesor Comercial:").strip()
                sup_asignado = st.selectbox("Supervisor Responsable:", tb_sups["Visualizacion"].tolist())
                
                if st.form_submit_button("💾 Vincular Asesor"):
                    if id_asesor_nuevo == "" or nom_asesor == "":
                        st.error("⚠️ El Código de Ruta (ID_Asesor) y el Nombre son estrictamente obligatorios.")
                    elif not tb_asesores.empty and "ID_Asesor" in tb_asesores.columns and id_asesor_nuevo in tb_asesores["ID_Asesor"].astype(str).str.strip().str.upper().values:
                        st.error(f"❌ El código de ruta **{id_asesor_nuevo}** ya existe en el sistema. Intente con otra.")
                    else:
                        id_sup_sel = tb_sups[tb_sups["Visualizacion"] == sup_asignado].iloc[0]["ID_Usuario"]
                        
                        nuevo_a = pd.DataFrame([{
                            "ID_Asesor": id_asesor_nuevo, 
                            "Nombre_Asesor": nom_asesor, 
                            "ID_Usuario": id_sup_sel
                        }])
                        
                        columnas_deseadas = ["ID_Asesor", "Nombre_Asesor", "ID_Usuario"]
                        if not tb_asesores.empty:
                            tb_asesores_filtrada = tb_asesores[[col for col in columnas_deseadas if col in tb_asesores.columns]]
                        else:
                            tb_asesores_filtrada = pd.DataFrame(columns=columnas_deseadas)
                        
                        df_final_asesores = pd.concat([tb_asesores_filtrada, nuevo_a], ignore_index=True)
                        df_final_asesores = df_final_asesores.reindex(columns=columnas_deseadas)
                        
                        st.session_state["mensaje_exito"] = f"🏃 ¡Asesor '{nom_asesor}' (Ruta: {id_asesor_nuevo}) vinculado con éxito!"
                        st.session_state["pestaña_activa"] = 2
                        st.cache_data.clear()
                        actualizar_tabla_excel(df_final_asesores, "T_Asesores")
        else:
            st.info("Debe dar de alta supervisores primero.")
            
        if mensaje_local and pestaña_activa_local == 2:
            st.success(mensaje_local)
            st.session_state["mensaje_exito"] = None
                            



    # ==========================================
    # PESTAÑA 3: VISOR Y EDICIÓN
    # ==========================================
    with pestana_config[3]:
        st.markdown("### 🔍 Panel de Modificación de Datos")
        sub_tabs = st.tabs(["🏢 Sucursales Registradas", "👤 Usuarios del Sistema", "🏃 Asesores por Supervisor"])
        
        with sub_tabs[0]:
            df_suc_visualizacion = tb_sucursales_completa[["ID_Sucursal", "Nombre_Sucursal", "Nombre_Region"]].copy() if not tb_sucursales_completa.empty else pd.DataFrame()
            edicion_suc_visual = st.data_editor(
                df_suc_visualizacion, use_container_width=True, hide_index=True, key="editor_suc",
                column_config={"Nombre_Region": st.column_config.SelectboxColumn("Región", options=tb_regiones["Nombre_Region"].tolist(), required=True)}
            )
            if st.button("💾 Guardar Cambios en Sucursales"):
                maestro_regiones = cargar_tabla_cached("T_Regiones")
                maestro_usuarios_db = cargar_tabla_cached("T_Usuarios")
                df_final_sucursales = edicion_suc_visual.merge(maestro_regiones, on="Nombre_Region", how="left")[["ID_Sucursal", "Nombre_Sucursal", "ID_Region"]]
                df_final_sucursales["ID_Region"] = df_final_sucursales["ID_Region"].fillna(0).astype(int)
                df_final_sucursales["ID_Sucursal"] = df_final_sucursales["ID_Sucursal"].astype(int)
                
                mapeo_suc_a_region_nueva = dict(zip(df_final_sucursales["ID_Sucursal"], df_final_sucursales["ID_Region"]))
                df_usuarios_actualizar = maestro_usuarios_db.copy()
                for index, fila_user in df_usuarios_actualizar.iterrows():
                    id_suc_usuario = int(fila_user["ID_Sucursal"])
                    if id_suc_usuario in mapeo_suc_a_region_nueva and id_suc_usuario != 0:
                        df_usuarios_actualizar.at[index, "ID_Region"] = int(mapeo_suc_a_region_nueva[id_suc_usuario])

                df_usuarios_actualizar["ID_Region"] = df_usuarios_actualizar["ID_Region"].astype(int)
                df_usuarios_actualizar["ID_Sucursal"] = df_usuarios_actualizar["ID_Sucursal"].astype(int)
                
                st.session_state["mensaje_exito"] = "🏢 ¡Cambios en Sucursales aplicados con éxito!"
                st.session_state["pestaña_activa"] = 3
                actualizar_tabla_excel(df_final_sucursales, "T_Sucursales")
                actualizar_tabla_excel(df_usuarios_actualizar, "T_Usuarios")

                
        with sub_tabs[1]:
            df_user_merge = tb_usuarios.merge(tb_rol, on="ID_Rol", how="left").merge(tb_regiones, on="ID_Region", how="left").merge(tb_sucursales, on="ID_Sucursal", how="left")
            df_user_visual = df_user_merge[["ID_Usuario", "Nombre", "User", "Clave", "Nombre_Rol", "Nombre_Region", "Nombre_Sucursal"]].copy()
            opciones_sucursales = ["Todas"] + tb_sucursales["Nombre_Sucursal"].tolist()

            edicion_user_visual = st.data_editor(
                df_user_visual, use_container_width=True, hide_index=True, key="editor_user",
                column_config={
                    "Nombre_Rol": st.column_config.SelectboxColumn("Rol / Cargo", options=tb_rol["Nombre_Rol"].tolist(), required=True),
                    "Nombre_Region": st.column_config.TextColumn("Región Asignada", disabled=True),
                    "Nombre_Sucursal": st.column_config.SelectboxColumn("Sucursal Asignada", options=opciones_sucursales, required=True)
                }
            )
            if st.button("💾 Guardar Cambios en Usuarios"):
                df_edicion_prep = edicion_user_visual.copy()
                df_edicion_prep["Nombre_Region"] = df_edicion_prep["Nombre_Region"].replace("Todas", "")
                df_edicion_prep["Nombre_Sucursal"] = df_edicion_prep["Nombre_Sucursal"].replace("Todas", "")
                
                df_guardar_u = df_edicion_prep.merge(tb_rol, on="Nombre_Rol", how="left").merge(tb_regiones, on="Nombre_Region", how="left").merge(tb_sucursales, on="Nombre_Sucursal", how="left")
                id_region_col = "ID_Region_y" if "ID_Region_y" in df_guardar_u.columns else "ID_Region"
                id_sucursal_col = "ID_Sucursal_y" if "ID_Sucursal_y" in df_guardar_u.columns else "ID_Sucursal"
                
                df_guardar_u[id_region_col] = df_guardar_u[id_region_col].fillna(0).astype(int)
                df_guardar_u[id_sucursal_col] = df_guardar_u[id_sucursal_col].fillna(0).astype(int)
                
                df_final_usuarios = df_guardar_u[["ID_Usuario", "Nombre", "User", "Clave", "ID_Rol", id_region_col, id_sucursal_col]].rename(
                    columns={id_region_col: "ID_Region", id_sucursal_col: "ID_Sucursal"}
                )
                
                for index, fila in df_final_usuarios.iterrows():
                    usuario_original = tb_usuarios[tb_usuarios["ID_Usuario"] == fila["ID_Usuario"]]
                    if not usuario_original.empty:
                        rol_original = int(usuario_original["ID_Rol"].values[0])
                        if rol_original in [1, 2]:
                            df_final_usuarios.at[index, "ID_Region"] = int(usuario_original["ID_Region"].values[0])
                            df_final_usuarios.at[index, "ID_Sucursal"] = int(usuario_original["ID_Sucursal"].values[0])
                
                st.session_state["mensaje_exito"] = "👤 ¡Estructura de Usuarios actualizada con éxito!"
                st.session_state["pestaña_activa"] = 3
                actualizar_tabla_excel(df_final_usuarios, "T_Usuarios")

                
        with sub_tabs[2]:
            lista_supervisores = tb_usuarios[tb_usuarios["ID_Rol"] == 3].copy()
            if not lista_supervisores.empty:
                sup_elegido_nom = st.selectbox("Seleccione un Supervisor:", lista_supervisores["Nombre"].tolist())
                id_sup_elegido = lista_supervisores[lista_supervisores["Nombre"] == sup_elegido_nom].iloc[0]["ID_Usuario"]
                asesores_del_sup = tb_asesores[tb_asesores["ID_Usuario"] == id_sup_elegido].copy()
                if not asesores_del_sup.empty:
                    edicion_ase_parcial = st.data_editor(asesores_del_sup[["ID_Asesor", "Nombre_Asesor"]], use_container_width=True, hide_index=True)
                    if st.button("💾 Guardar Modificaciones de Asesores"):
                        tb_asesores_actualizada = tb_asesores.copy()
                        for _, fila in edicion_ase_parcial.iterrows():
                            tb_asesores_actualizada.loc[tb_asesores_actualizada["ID_Asesor"] == fila["ID_Asesor"], "Nombre_Asesor"] = fila["Nombre_Asesor"]
                        st.session_state["mensaje_exito"] = "🏃 ¡Asesores actualizados con éxito!"
                        st.session_state["pestaña_activa"] = 3
                        actualizar_tabla_excel(tb_asesores_actualizada, "T_Asesores")

                else:
                    st.info("Este supervisor no tiene asesores asignados.")
            else:
                st.info("No hay supervisores en el sistema.")
                
        if mensaje_local and pestaña_activa_local == 3:
            st.success(mensaje_local)
            st.session_state["mensaje_exito"] = None
