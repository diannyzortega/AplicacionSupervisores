# src/views/categorias.py
import streamlit as st
import pandas as pd
from src.database.queries import cargar_tabla_cached, actualizar_tabla_excel

def show_categorias():
    st.title("🏷️ Configuración de Categorías Foco")
    st.markdown("<p style='color: #A0AAB2;'>Gestión de categorías, unidades de activación y objetivos por región</p>", unsafe_allow_html=True)
    st.write("---")
    
    # 1. Cargar tablas de base de datos
    tb_categorias = cargar_tabla_cached("T_Categorias")
    tb_regiones = cargar_tabla_cached("T_Regiones")
    
    # 2. Mapear rol y región del usuario actual
    rol_raw = str(st.session_state.get("rol_actual", "asesor")).replace(".0", "").strip().lower()
    if rol_raw == "1" or rol_raw == "admin" or rol_raw == "administrador":
        rol = "administrador"
    elif rol_raw == "2" or rol_raw == "coordinador":
        rol = "coordinador"
    else:
        rol = "supervisor"
        
    region_usuario = st.session_state.get("region_usuario", "").strip()
    
    # Buscar el ID de Región para coordinadores
    id_region_usuario = 0
    if rol == "coordinador" and not tb_regiones.empty:
        match_reg = tb_regiones[tb_regiones["Nombre_Region"].astype(str).str.lower() == region_usuario.lower()]
        if not match_reg.empty:
            id_region_usuario = int(match_reg.iloc[0]["ID_Region"])
            
    # 3. Inicializar mensajes y pestaña activa
    if "mensaje_cat_exito" not in st.session_state:
        st.session_state["mensaje_cat_exito"] = None
    if "pestaña_cat_activa" not in st.session_state:
        st.session_state["pestaña_cat_activa"] = 0
        
    mensaje_local = st.session_state.get("mensaje_cat_exito")
    pestaña_activa_local = st.session_state.get("pestaña_cat_activa", 0)
    
    # Mostrar notificaciones locales si existen
    # (Se manejarán localmente al final de cada pestaña)

    # Pestañas adaptativas: Administrador solo ve la pestaña de Edición/Visor, Coordinador ambas
    if rol == "administrador":
        pestanas = st.tabs(["🔍 Visor y Edición de Categorías"])
    else:
        pestanas = st.tabs(["🆕 Crear Categoría Foco", "🔍 Visor y Edición de Categorías"])

    # Función interna para reutilizar el renderizado del Visor y Edición
    def render_visor_edicion(index_pestana_guardar):
        st.subheader("Modificar Categorías")
        
        # Filtrar categorías visibles según el rol del coordinador
        if rol == "coordinador":
            df_filtrado = tb_categorias[tb_categorias["ID_Region"].isin([id_region_usuario, 0])].copy()
        else:
            df_filtrado = tb_categorias.copy()
            
        if df_filtrado.empty:
            st.info("No hay categorías configuradas para mostrar.")
        else:
            # Cruzar con regiones para mostrar el nombre legible de la región
            if not tb_regiones.empty:
                df_visual = df_filtrado.merge(tb_regiones, on="ID_Region", how="left")
                df_visual["Nombre_Region"] = df_visual["Nombre_Region"].fillna("Todas")
            else:
                df_visual = df_filtrado.copy()
                df_visual["Nombre_Region"] = "Todas"
                
            # Seleccionar y ordenar columnas para el visor
            columnas_orden = ["ID_Categoria", "Nombre_Categoria", "Nombre_Region", "Mes", "Obj_Activacion", "Tipo_Obj_Activacion", "Obj_Volumen", "Obj_Profundidad"]
            df_visual = df_visual[[col for col in columnas_orden if col in df_visual.columns]]
            
            # Configurar las columnas del editor de datos
            opciones_reg_select = ["Todas"] + tb_regiones["Nombre_Region"].tolist() if not tb_regiones.empty else ["Todas"]
            
            config_columnas = {
                "ID_Categoria": st.column_config.NumberColumn("ID", disabled=True),
                "Nombre_Categoria": st.column_config.TextColumn("Nombre Categoría", required=True),
                "Nombre_Region": st.column_config.SelectboxColumn("Región Asignada", options=opciones_reg_select, required=True, disabled=(rol == "coordinador")),
                "Mes": st.column_config.SelectboxColumn("Mes", options=["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"], required=True),
                "Obj_Activacion": st.column_config.NumberColumn("Meta Activación", required=True),
                "Tipo_Obj_Activacion": st.column_config.SelectboxColumn("Unidad Activación", options=["Porcentaje", "Cantidad"], required=True),
                "Obj_Volumen": st.column_config.NumberColumn("Meta Volumen (%)"),
                "Obj_Profundidad": st.column_config.NumberColumn("Meta Profundidad (U)")
            }
            
            edicion_visual = st.data_editor(
                df_visual,
                use_container_width=True,
                hide_index=True,
                column_config=config_columnas,
                key=f"editor_categorias_foco_{rol}"
            )
            
            if st.button("💾 Guardar Cambios en Categorías", key=f"btn_save_edicion_cats_{rol}"):
                # Hacer una copia del maestro original de categorías
                df_maestro_actualizado = tb_categorias.copy()
                
                # Iterar sobre las filas editadas y actualizar en el maestro
                for index, fila in edicion_visual.iterrows():
                    id_cat = int(fila["ID_Categoria"])
                    nom_cat = str(fila["Nombre_Categoria"]).strip()
                    obj_act_val = int(fila["Obj_Activacion"])
                    tipo_act = str(fila["Tipo_Obj_Activacion"])
                    vol = float(fila["Obj_Volumen"])
                    prof = int(fila["Obj_Profundidad"])
                    mes_val = str(fila.get("Mes", "")).strip()
                    
                    # Buscar el ID de la Región
                    reg_nombre = str(fila.get("Nombre_Region", "Todas"))
                    if reg_nombre == "Todas" or tb_regiones.empty:
                        id_reg = 0
                    else:
                        match_r = tb_regiones[tb_regiones["Nombre_Region"] == reg_nombre]
                        id_reg = int(match_r.iloc[0]["ID_Region"]) if not match_r.empty else 0
                    
                    # Si el usuario es coordinador, forzamos que no altere la región original
                    if rol == "coordinador":
                        # Mantener el ID_Region que tenía originalmente
                        orig_cat = tb_categorias[tb_categorias["ID_Categoria"] == id_cat]
                        if not orig_cat.empty:
                            id_reg = int(orig_cat.iloc[0]["ID_Region"])
                            
                    # Actualizar en la copia del maestro
                    if id_cat in df_maestro_actualizado["ID_Categoria"].values:
                        idx_maestro = df_maestro_actualizado[df_maestro_actualizado["ID_Categoria"] == id_cat].index[0]
                        df_maestro_actualizado.at[idx_maestro, "Nombre_Categoria"] = nom_cat
                        df_maestro_actualizado.at[idx_maestro, "ID_Region"] = id_reg
                        df_maestro_actualizado.at[idx_maestro, "Obj_Activacion"] = obj_act_val
                        df_maestro_actualizado.at[idx_maestro, "Tipo_Obj_Activacion"] = tipo_act
                        df_maestro_actualizado.at[idx_maestro, "Obj_Volumen"] = vol
                        df_maestro_actualizado.at[idx_maestro, "Obj_Profundidad"] = prof
                        df_maestro_actualizado.at[idx_maestro, "Mes"] = mes_val
                
                # Guardar en base de datos
                df_maestro_actualizado["ID_Region"] = df_maestro_actualizado["ID_Region"].fillna(0).astype(int)
                msg = "🏷️ ¡Maestro de Categorías guardado y sincronizado!"
                st.session_state["mensaje_cat_exito"] = msg
                st.session_state["pestaña_cat_activa"] = index_pestana_guardar
                st.toast(msg, icon="💾")
                st.cache_data.clear()
                actualizar_tabla_excel(df_maestro_actualizado, "T_Categorias")
                
        if mensaje_local and pestaña_activa_local == index_pestana_guardar:
            st.success(mensaje_local)
            st.session_state["mensaje_cat_exito"] = None

    # ==========================================
    # RENDERIZADO DE LAS PESTAÑAS SEGÚN ROL
    # ==========================================
    if rol == "administrador":
        with pestanas[0]:
            render_visor_edicion(index_pestana_guardar=0)
    else:
        # Coordinador tiene las dos pestañas
        with pestanas[0]:
            st.subheader("Cargar Nueva Categoría")
            siguiente_id_cat = int(tb_categorias["ID_Categoria"].max() + 1) if not tb_categorias.empty else 1
            
            with st.form("Form_Crear_Cat", clear_on_submit=True):
                nom_categoria = st.text_input("Nombre de la Categoría:", placeholder="Ej. Cocidos Rebanables, Salsas, etc.").strip()
                mes_categoria = st.selectbox("Mes de la Categoría Foco:", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
                st.text_input("Región Asignada (Automática):", value=region_usuario if region_usuario else "Sin Región", disabled=True)
                id_region_sel = id_region_usuario
                
                st.markdown("##### 🎯 Configuración de Objetivos")
                st.markdown("**1. Objetivo de Activación** *(Flexible)*")
                col_act1, col_act2 = st.columns(2)
                with col_act1:
                    obj_act = st.text_input("Valor Activación:", placeholder="Ej. 85 o 10", key="cat_act_val_c")
                with col_act2:
                    tipo_obj_act = st.selectbox("Unidad Activación:", ["Porcentaje", "Cantidad"], index=0, key="cat_act_tipo_c")
                    
                st.write("---")
                
                col_vol, col_prof = st.columns(2)
                with col_vol:
                    st.markdown("**2. Objetivo de Volumen**")
                    obj_vol = st.number_input("Meta Volumen (%):", min_value=0.0, max_value=100.0, value=0.0, step=5.0, help="Dejar en 0 si no aplica objetivo de volumen")
                with col_prof:
                    st.markdown("**3. Profundidad de Línea**")
                    obj_prof = st.number_input("Meta Profundidad (Unidades):", min_value=0, value=0, step=1, help="Dejar en 0 si no aplica profundidad de línea")

                if st.form_submit_button("💾 Guardar Categoría"):
                    if nom_categoria == "":
                        st.error("❌ El nombre de la categoría no puede estar vacío.")
                    elif obj_act.strip() == "":
                        st.error("❌ Debe asignar un valor al objetivo de Activación.")
                    else:
                        # Validar si ya existe la categoría para esta misma región
                        existe = False
                        if not tb_categorias.empty:
                            duplicados = tb_categorias[
                                (tb_categorias["Nombre_Categoria"].str.lower() == nom_categoria.lower()) & 
                                (tb_categorias["ID_Region"] == id_region_sel)
                            ]
                            if not duplicados.empty:
                                existe = True
                        
                        if existe:
                            st.error(f"❌ Esta categoría ya se encuentra registrada para la región seleccionada.")
                        else:
                            valor_act_limpio = obj_act.replace("%", "").strip()
                            
                            nueva_cat = pd.DataFrame([{
                                "ID_Categoria": siguiente_id_cat, 
                                "Nombre_Categoria": nom_categoria,
                                "ID_Region": id_region_sel,
                                "Obj_Activacion": valor_act_limpio,
                                "Tipo_Obj_Activacion": tipo_obj_act,
                                "Obj_Volumen": float(obj_vol),
                                "Obj_Profundidad": int(obj_prof),
                                "Mes": mes_categoria
                            }])
                            
                            df_actualizado_cat = pd.concat([tb_categorias, nueva_cat], ignore_index=True)
                            df_actualizado_cat["ID_Region"] = df_actualizado_cat["ID_Region"].fillna(0).astype(int)
                            
                            # Guardar estados y sincronizar
                            msg = f"🏷️ Categoría '{nom_categoria}' creada con éxito."
                            st.session_state["mensaje_cat_exito"] = msg
                            st.session_state["pestaña_cat_activa"] = 0
                            st.toast(msg, icon="🏷️")
                            st.cache_data.clear()
                            actualizar_tabla_excel(df_actualizado_cat, "T_Categorias")
                            
            if mensaje_local and pestaña_activa_local == 0:
                st.success(mensaje_local)
                st.session_state["mensaje_cat_exito"] = None
                            
        with pestanas[1]:
            render_visor_edicion(index_pestana_guardar=1)
