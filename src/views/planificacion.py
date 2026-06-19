# src/views/planificacion.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import time
from src.database.queries import cargar_tabla_cached, actualizar_tabla_excel

# ---- Helper functions for keeping closures in sync ----

def has_linked_cierre(fecha_str: str, supervisor: str) -> bool:
    """Check if a cierre (result) already exists for the given date and supervisor.
    If a cierre exists, the planning entry must not be edited.
    """
    df_cierres = cargar_tabla_cached("Resultados_Tarde")
    if df_cierres.empty:
        return False
    filtro = (df_cierres["Fecha_Cierre"].astype(str).str.strip() == fecha_str) & (df_cierres["Supervisor"] == supervisor)
    return not df_cierres[filtro].empty

# ---- Helper functions for keeping closures in sync ----

def show_planificacion():
    st.title("📝 Monitor de Planificación Semanal")
    st.markdown("<p style='color: #A0AAB2;'>Registro de Planificacion Semanal de supervisores</p>", unsafe_allow_html=True)
    st.write("---")

    df_historico_plan = cargar_tabla_cached("Planificacion_Semanal")
    tb_asesores = cargar_tabla_cached("T_Asesores")

    tb_regiones = cargar_tabla_cached("T_Regiones")
    
    # Obtener rol actual
    rol = str(st.session_state.get("rol_actual", "asesor")).replace(".0", "").strip().lower()
    if rol == "1":
        rol = "administrador"
    elif rol == "2":
        rol = "coordinador"
    elif rol == "3":
        rol = "supervisor"

    if rol in ["administrador", "coordinador"]:
            
            if df_historico_plan.empty:
                st.info("No hay planificaciones guardadas en la base de datos.")
            else:
                if rol == "coordinador":
                    region_perfil = st.session_state["region_usuario"]
                    st.info(f"📋 Mostrando planificaciones de la Región: **{region_perfil}**")
                    df_filtrado_perfil = df_historico_plan[df_historico_plan["Región"] == region_perfil].copy()
                else:
                    df_filtrado_perfil = df_historico_plan.copy()
                    
                # --- BLOQUE DE FILTROS SUPERIORES INTERACTIVOS ---
                with st.container(border=True):
                    col_m1, col_m2, col_m3 = st.columns([1.5, 1.5, 2])
                    with col_m1:
                        fechas_disponibles = sorted(df_filtrado_perfil["Fecha"].dropna().unique(), reverse=True)
                        fecha_sel = st.selectbox("Filtrar por Fecha de Jornada:", ["Todas las Fechas"] + list(fechas_disponibles))
                    with col_m2:
                        if rol == "administrador":
                            regiones_disp = ["Todas"] + list(df_filtrado_perfil["Región"].dropna().unique())
                            reg_sel = st.selectbox("Filtrar por Región:", regiones_disp)
                            if reg_sel != "Todas":
                                df_filtrado_perfil = df_filtrado_perfil[df_filtrado_perfil["Región"] == reg_sel]
                        
                        sucursales_disp = ["Todas"] + list(df_filtrado_perfil["Sucursal"].dropna().unique())
                        suc_sel = st.selectbox("Filtrar por Sucursal:", sucursales_disp)
                        if suc_sel != "Todas":
                            df_filtrado_perfil = df_filtrado_perfil[df_filtrado_perfil["Sucursal"] == suc_sel]
                    with col_m3:
                        busqueda = st.text_input("🔍 Buscar por Supervisor o Asesor Comercial:", placeholder="Ej: Jhon, Equipo A1...")

                # Aplicación de segmentaciones secundarias
                if fecha_sel != "Todas las Fechas":
                    df_filtrado_perfil = df_filtrado_perfil[df_filtrado_perfil["Fecha"] == fecha_sel]
                if busqueda.strip() != "":
                    termino = busqueda.lower().strip()
                    df_filtrado_perfil = df_filtrado_perfil[
                        df_filtrado_perfil["Supervisor"].astype(str).str.lower().str.contains(termino) | 
                        df_filtrado_perfil["Asesor"].astype(str).str.lower().str.contains(termino)
                    ]
                
                st.write("")
                st.markdown(f"**Registros encontrados:** `{len(df_filtrado_perfil)}`")
                
                # --- FUNCIÓN DISPARADORA DEL MODAL EMERGENTE PREMIUM (CORREGIDA ANTI-NAN) ---
                @st.dialog("🔍 Detalle Completo de Planificación")
                def abrir_detalle_planificacion(datos_fila):
                    import pandas as pd
                    modalidad = datos_fila.get('Modalidad', 'Acompañamiento en Calle')
                    es_campo = modalidad in ["Acompañamiento en Calle", "Auditoria de Ruta"]

                    # 🛡️ Blindaje anti-NaN para el nombre del Asesor Comercial
                    val_asesor = datos_fila.get('Asesor')
                    # Detect if there is no advisor (blank, NaN, N/A, etc.)
                    fue_solo = pd.isna(val_asesor) or str(val_asesor).strip().lower() in ["nan", "", "none", "n/a", "na", "no especificado"]
                    if fue_solo:
                        nombre_asesor_mostrar = "No hubo acompañamiento (Gestión Solo)"
                    else:
                        nombre_asesor_mostrar = str(val_asesor).strip()

                    if es_campo and not fue_solo:
                        st.markdown(f"### Asesor: **{nombre_asesor_mostrar}**")
                    else:
                        st.markdown(f"### Actividad: **{modalidad}**")    
                    st.caption(f"Registrado por Supervisor: {datos_fila.get('Supervisor', 'N/A')} | Región: {datos_fila.get('Región', 'N/A')}")
                    st.write("---")
                    
                    # Secciones adaptativas según el tipo de modalidad
                    if es_campo:
                        st.markdown("##### 📍 Logística de Campo")
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown(f"**🏢 Sucursal:** {datos_fila.get('Sucursal', 'N/A')}")
                            st.markdown(f"**⚙️ Modalidad:** {modalidad}")
                        with c2:
                            st.markdown(f"**🗺️ Zona / Ruta:** {datos_fila.get('Zona', 'N/A')}")
                            acompañado = datos_fila.get('Acompañamiento', 'No')
                            color_acomp = "#34d399" if acompañado == "Sí" else "#94a3b8"
                            st.markdown(f"**👥 Acompañamiento:** <span style='color:{color_acomp}; font-weight:bold;'>{acompañado}</span>", unsafe_allow_html=True)
                        
                        st.write("")
                        st.markdown("##### 🎯 Indicadores Clave y Cuotas Proyectadas")
                        m_col1, m_col2, m_col3 = st.columns(3)
                        with m_col1:
                            st.markdown(f"""<div style="background-color:#1e293b; padding:12px; border-radius:8px; border:1px solid #334155; text-align:center;">
                                <span style="font-size:11px; color:#94a3b8; font-weight:600; text-transform:uppercase;">Meta Cajas</span>
                                <h4 style="margin:4px 0 0 0; color:#ffffff;">{datos_fila.get('Cajas_Objetivo', 0):,.0f} Cjs</h4>
                            </div>""", unsafe_allow_html=True)
                        with m_col2:
                            st.markdown(f"""<div style="background-color:#1e293b; padding:12px; border-radius:8px; border:1px solid #334155; text-align:center;">
                                <span style="font-size:11px; color:#94a3b8; font-weight:600; text-transform:uppercase;">Meta Kilos</span>
                                <h4 style="margin:4px 0 0 0; color:#ffffff;">{datos_fila.get('Kilos_Objetivo', 0.0):,.1f} Kg</h4>
                            </div>""", unsafe_allow_html=True)
                        with m_col3:
                            st.markdown(f"""<div style="background-color:#1e293b; padding:12px; border-radius:8px; border:1px solid #334155; text-align:center;">
                                <span style="font-size:11px; color:#34d399; font-weight:600; text-transform:uppercase;">Proyección Cobro</span>
                                <h4 style="margin:4px 0 0 0; color:#34d399;">${datos_fila.get('Monto_Proyectado_Cobro', 0.0):,.2f}</h4>
                            </div>""", unsafe_allow_html=True)
                        
                        st.write("")
                        st.markdown("##### 🔍 Segmentación de Ruta")
                        cr1, cr2 = st.columns(2)
                        with cr1:
                            st.markdown(f"**👥 Clientes en Ruta:** {datos_fila.get('Clientes_Actuales', 0)}")
                            st.markdown(f"**🚀 Clientes a Captar:** {datos_fila.get('Clientes_Captar', 0)}")
                        
                        with cr2:
                            enf_val = datos_fila.get('Enfoque')
                            mostrar_enf = pd.notna(enf_val) and str(enf_val).strip().lower() not in ["nan", "", "none", "no definido"]
                            
                            if mostrar_enf:
                                st.markdown(f"**📈 Enfoque Comercial:** {enf_val}")

                        aud_j = "Sí" if datos_fila.get('Auditoria_Jamones', False) else "No"
                        aud_q = "Sí" if datos_fila.get('Auditoria_Quesos', False) else "No"
                        if aud_j == "Sí" or aud_q == "Sí":
                            st.write("")
                            st.markdown("##### 🏆 Concursos Auditados")
                            ca1, ca2 = st.columns(2)
                            ca1.markdown(f"**🍖 Concurso Jamones:** {aud_j}")
                            ca2.markdown(f"**🧀 Concurso Quesos:** {aud_q}")
                    
                    else:
                        st.markdown("##### 📍 Logística Operativa")
                        with st.container():
                            st.markdown(f"**🏢 Sucursal:** {datos_fila.get('Sucursal', 'N/A')}")
                            st.markdown(f"**⚙️ Modalidad:** {modalidad}")
                        
                        st.write("")
                        st.markdown("##### 💰 Presupuesto de Recuperación Financiera")
                        st.markdown(f"""<div style="background-color:#1e293b; padding:16px; border-radius:8px; border:1px solid #334155; text-align:center; max-width: 300px; margin: 0 auto;">
                            <span style="font-size:12px; color:#34d399; font-weight:600; text-transform:uppercase;">Monto Recuperación Proyectado</span>
                            <h3 style="margin:6px 0 0 0; color:#34d399;">${datos_fila.get('Monto_Proyectado_Cobro', 0.0):,.2f}</h3>
                        </div>""", unsafe_allow_html=True)

                    st.write("")
                    with st.container(border=True):
                        titulo_objetivo = "🎯 Objetivo Primordial de la Jornada:" if es_campo else "📝 Detalle de la Actividad Planificada:"
                        st.markdown(f"**{titulo_objetivo}**")
                        
                        # Limpieza extra por si el objetivo también arroja NaN en rutas administrativas vacías
                        obj_val = datos_fila.get('Objetivo_Principal')
                        if pd.isna(obj_val) or str(obj_val).strip().lower() in ["nan", ""]:
                            obj_val = 'Sin observaciones adicionales.'
                        st.markdown(f"*{obj_val}*")
                    
                    st.write("")
                    if st.button("Cerrar Ventana", use_container_width=True, key="btn_close_plan_modal"):
                        st.rerun()

                # --- DISEÑO DE TABLA COMPACTA LIMPIA ---
                if not df_filtrado_perfil.empty:
                    st.markdown("""
                        <div style="background-color: #1e293b; padding: 10px 16px; border-radius: 8px 8px 0px 0px; border: 1px solid #334155; margin-bottom: 4px;">
                            <div style="display: flex; font-weight: bold; color: #cbd5e1; font-size: 14px;">
                                <div style="flex: 1.2;">📅 Fecha</div>
                                <div style="flex: 2;">👤 Responsable</div>
                                <div style="flex: 1.5;">🏢 Sucursal</div>
                                <div style="flex: 3.5;">🏃 Tipo de Actividad</div>
                                <div style="flex: 2;">🎯 Objetivo</div>
                                <div style="flex: 1.3; text-align: center;">🔍 Acción</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                    for idx, fila in df_filtrado_perfil.reset_index(drop=True).iterrows():
                        with st.container():
                            col1, col2, col3, col4, col5, col6 = st.columns([1.2, 2, 1.5, 3.5, 2, 1.3])
                            
                            with col1:
                                st.markdown(f"<p style='margin-top:6px; font-size:14px;'>{fila.get('Fecha', 'N/A')}</p>", unsafe_allow_html=True)
                            
                            with col2:
                                supervisor_visual = fila.get('Supervisor', 'N/A')
                                st.markdown(f"<p style='margin-top:6px; font-size:14px; font-weight:600;'>{supervisor_visual}</p>", unsafe_allow_html=True)
                            
                            with col3:
                                st.markdown(f"<p style='margin-top:6px; font-size:14px; color:#94a3b8;'>{fila.get('Sucursal', 'N/A')}</p>", unsafe_allow_html=True)
                            
                            with col4:
                                modalidad_texto = fila.get('Modalidad', 'No especificada')
                                if modalidad_texto in ["Acompañamiento en Calle", "Auditoria de Ruta"]:
                                    color_badge = "#38bdf8"
                                elif modalidad_texto == "Gestion Administrativa":
                                    color_badge = "#fbbf24"
                                else:
                                    color_badge = "#a78bfa"
                                    
                                st.markdown(f"<p style='margin-top:6px; font-size:13px; font-weight:500; color:{color_badge};'>{modalidad_texto}</p>", unsafe_allow_html=True)
                            
                            with col5:
                                objetivo_txt = fila.get('Objetivo_Principal', 'Sin objetivo')
                                st.markdown(f"<p style='margin-top:6px; font-size:13px; color:#94a3b8;'>{objetivo_txt}</p>", unsafe_allow_html=True)
                            
                            with col6:
                                if st.button("Ver Detalle", key=f"btn_mon_plan_{idx}", use_container_width=True):
                                    abrir_detalle_planificacion(fila)

                            st.markdown("<hr style='margin:4px 0; border-color:#1e293b;'>", unsafe_allow_html=True)

    else:
            # =========================================================
            # ENTRADA DE DATOS: PERFIL SUPERVISORES COMERCIALES
            # =========================================================
            suc_selec = st.session_state["sucursal_usuario"]
            region_nombre = st.session_state["region_usuario"]
            supervisor_nombre = st.session_state["usuario_actual"]
            id_supervisor_activo = st.session_state["id_usuario_actual"]
            
            if "msg_exito_crear" in st.session_state:
                st.success(st.session_state["msg_exito_crear"])
                del st.session_state["msg_exito_crear"]
                
            st.info(f"🌍 **Región:** {region_nombre} | 📍 **Sucursal:** {suc_selec} | 👤 **Equipo:** {supervisor_nombre}")

            pestaña_crear, pestaña_editar = st.tabs(["🆕 Nueva Planificación", "✏️ Modificar Planificación"])

            # PESTAÑA 1: NUEVA PLANIFICACIÓN
            with pestaña_crear:
                st.subheader("Cargar Nueva Planificación Diaria")
                fecha_planificada_nueva = st.date_input("Fecha de la Jornada a Planificar:", value=datetime.now().date(), key="fecha_nueva_plan")
                
                sufijo_p = str(fecha_planificada_nueva)
                
                st.markdown("### 🏃 Modalidad de Trabajo")
                options_jornada = ["Acompañamiento en Calle", "Auditoria de Ruta", "Gestion Administrativa", "Otros"]
                ubicacion_nueva = st.selectbox("¿Qué tipo de jornada realizará hoy?", options_jornada, key=f"ubicacion_nueva_plan_{sufijo_p}")
                
                acompañamiento_n, asesor_seleccionado_n, zona_inspeccion_n = "No", "N/A", "N/A"
                clientes_actuales_n, clientes_a_captar_n = 25, 0
                foco_dia_n, enfoques_seleccionados_n = "", []
                auditar_concurso_a_n, auditar_concurso_b_n = False, False
                monto_proyectado_n, cajas_objetivo_n, kilos_objetivo_n = 0.0, 0, 0.0

                if ubicacion_nueva in ["Acompañamiento en Calle", "Auditoria de Ruta"]:
                    col_a1, col_a2 = st.columns(2)
                    with col_a1:
                        acompañamiento_n = st.radio("¿Harás acompañamiento directo a un asesor?", ["No", "Sí"], key=f"acomp_n_{sufijo_p}")
                        if acompañamiento_n == "Sí":
                            asesores_filtrados = tb_asesores[tb_asesores["ID_Usuario"].astype(str) == str(id_supervisor_activo)]["Nombre_Asesor"].tolist()
                            if asesores_filtrados: 
                                asesor_seleccionado_n = st.selectbox("Selecciona el Asesor:", asesores_filtrados, key=f"ase_n_{sufijo_p}")
                            else:
                                st.warning("⚠️ Sin asesores.")
                                asesor_seleccionado_n = "N/A"
                        else:
                            asesor_seleccionado_n = "N/A"
                        
                        zona_inspeccion_n = st.text_input("📍 Especifique la Zona de visita:", key=f"zona_n_{sufijo_p}")
                    
                    with col_a2:
                        clientes_actuales_n = st.number_input("Cantidad de Clientes en Ruta/Zona para Hoy:", min_value=0, value=25, step=1, key=f"clt_act_n_{sufijo_p}")
                        
                        if 0 < clientes_actuales_n < 25:
                            falta = 25 - clientes_actuales_n
                            clientes_a_captar_n = st.number_input("Clientes a captar hoy (Calculado para óptimo):", min_value=0, max_value=25, value=falta, key=f"clt_cap_n_{sufijo_p}")
                        elif clientes_actuales_n >= 25:
                            st.success("✅ ¡Ruta óptima!")
                            clientes_a_captar_n = 0
                        else:
                            clientes_a_captar_n = st.number_input("Clientes a captar hoy:", min_value=0, value=0, key=f"clt_cap_n_cero_{sufijo_p}")

                    st.markdown("### 🎯 Estrategia y Foco Comercial")
                    foco_dia_n = st.text_area("Objetivo Principal del Día:", key=f"foco_n_{sufijo_p}")
                    
                    opciones_enfoque = ["Barrido(Captación)", "Desarrollo(Oportunidad)"]
                    enfoques_seleccionados_n = st.multiselect("Enfoque:", opciones_enfoque, key=f"enf_s_n_{sufijo_p}")
                    
                    st.markdown("#### 🏆 Auditoría de Concursos")
                    col_con1, col_con2 = st.columns(2)
                    auditar_concurso_a_n = col_con1.checkbox("Auditar Concurso de Jamones", key=f"aud_j_n_{sufijo_p}")
                    auditar_concurso_b_n = col_con2.checkbox("Auditar Concurso de Quesos", key=f"aud_q_n_{sufijo_p}")
                    
                    st.markdown("### 📦 Proyección de Cuotas")
                    col_v1, col_v2, col_v3 = st.columns(3)
                    monto_proyectado_n = col_v1.number_input("Cobranza ($):", min_value=0.0, value=0.0, key=f"monto_n_{sufijo_p}")
                    cajas_objetivo_n = col_v2.number_input("Meta Cajas:", min_value=0, value=0, key=f"cajas_n_{sufijo_p}")
                    kilos_objetivo_n = col_v3.number_input("Meta Kilos:", min_value=0.0, value=0.0, key=f"kilos_n_{sufijo_p}")

                elif ubicacion_nueva == "Gestion Administrativa":
                    st.markdown("### 🏢 Gestión Administrativa")
                    with st.container(border=True):
                        st.write("**💰 Presupuesto de Recuperación**")
                        monto_proyectado_n = st.number_input("Monto de Cobranza Vencida del Día ($):", min_value=0.0, value=0.0, key=f"monto_adm_n_{sufijo_p}")
                    
                    opciones_admin = ["Carga de objetivos", "Carga de Comisiones", "Cierre de quincena", "Cierre de mes"]
                    sub_tarea_admin = st.selectbox("Seleccione la actividad:", opciones_admin, key=f"sub_admin_n_{sufijo_p}")
                    detalle_admin = st.text_area("Detalle de la actividad:", key=f"det_admin_n_{sufijo_p}")
                    foco_dia_n = f"Admin: {sub_tarea_admin} - Detalle: {detalle_admin}"
                    clientes_actuales_n, clientes_a_captar_n = 0, 0
                    cajas_objetivo_n, kilos_objetivo_n = 0, 0.0

                elif ubicacion_nueva == "Otros":
                    st.markdown("### 📝 Otras Actividades")
                    with st.container(border=True):
                        st.write("**💰 Presupuesto de Recuperación**")
                        monto_proyectado_n = st.number_input("Monto de Cobranza Vencida del Día ($):", min_value=0.0, value=0.0, key=f"monto_otr_n_{sufijo_p}")
                        
                    actividad_otros = st.text_input("Detalle de la actividad:", key=f"otr_act_n_{sufijo_p}")
                    foco_dia_n = f"Otro: {actividad_otros}"
                    clientes_actuales_n, clientes_a_captar_n = 0, 0
                    cajas_objetivo_n, kilos_objetivo_n = 0, 0.0

                st.write("---")
                if st.button("🚀 Guardar Nueva Planificación", use_container_width=True, key=f"btn_guardar_nuevo_{sufijo_p}"):
                    fecha_str = str(fecha_planificada_nueva)
                    existe_duplicado = False
                    if not df_historico_plan.empty:
                        coordinencias = df_historico_plan[(df_historico_plan["Supervisor"] == supervisor_nombre) & (df_historico_plan["Fecha"].astype(str) == fecha_str)]
                        if not coordinencias.empty: 
                            existe_duplicado = True
                    
                    if existe_duplicado:
                        st.error(f"❌ Error: Ya cargaste una planificación para la fecha ({fecha_str}).")
                    else:
                        str_enfoques = ",".join(enfoques_seleccionados_n) if 'enfoques_seleccionados_n' in locals() else ""
                        
                        nuevo_registro = {
                            "Fecha": fecha_str, "Supervisor": supervisor_nombre, "Región": region_nombre, "Sucursal": suc_selec,
                            "Modalidad": ubicacion_nueva, "Acompañamiento": acompañamiento_n, "Asesor": asesor_seleccionado_n,
                            "Zona": zona_inspeccion_n, "Clientes_Actuales": int(clientes_actuales_n), "Clientes_Captar": int(clientes_a_captar_n),
                            "Objetivo_Principal": foco_dia_n, "Enfoque": str_enfoques,
                            "Auditoria_Jamones": 1 if auditar_concurso_a_n else 0, "Auditoria_Quesos": 1 if auditar_concurso_b_n else 0,
                            "Monto_Proyectado_Cobro": monto_proyectado_n, "Cajas_Objetivo": cajas_objetivo_n, "Kilos_Objetivo": kilos_objetivo_n,
                        }
                        df_final_actualizado = pd.concat([df_historico_plan, pd.DataFrame([nuevo_registro])], ignore_index=True)
                        st.session_state["msg_exito_crear"] = f"🚀 ¡Planificación del {fecha_str} guardada con éxito!"
                        espacio_mensaje_abajo_crear = st.empty()
                        if "msg_exito_crear" in st.session_state:
                            espacio_mensaje_abajo_crear.success(st.session_state["msg_exito_crear"])

                        # Subida limpia a Google Sheets (que internamente hace el clearing y el rerun)
                        actualizar_tabla_excel(df_final_actualizado, "Planificacion_Semanal")


                # PESTAÑA 2: MODIFICAR PLANIFICACIÓN
            with pestaña_editar:
                st.subheader("Panel de Modificación de Datos")
                planes_usuario = df_historico_plan[df_historico_plan["Supervisor"] == supervisor_nombre] if not df_historico_plan.empty else pd.DataFrame()

                if planes_usuario.empty:
                    st.info("Aún no tienes planificaciones registradas para modificar.")
                else:
                        fechas_disponibles = sorted(planes_usuario["Fecha"].dropna().unique(), reverse=True)
                        fecha_a_corregir = st.selectbox("Seleccione la fecha de la planificación:", ["-- Seleccionar Fecha --"] + list(fechas_disponibles), key="sb_fecha_edit")
                        
                        if fecha_a_corregir != "-- Seleccionar Fecha --":
                            datos_originales = planes_usuario[planes_usuario["Fecha"] == fecha_a_corregir].iloc[0].to_dict()
                            st.warning(f"⚠️ Editando fecha: {fecha_a_corregir}")
                            
                            sufijo = str(fecha_a_corregir)
                            
                            acompañado_e = datos_originales.get("Acompañamiento", "No")
                            enfoques_seleccionados_e = []
                            auditar_concurso_a_e, auditar_concurso_b_e = False, False
                            clientes_actuales_e, clientes_a_captar_e = 0, 0
                            cajas_objetivo_e, kilos_objetivo_e = 0, 0.0
                            
                            ubicacion_def = datos_originales.get("Modalidad", "Acompañamiento en Calle")
                            opciones_jornada = ["Acompañamiento en Calle", "Auditoria de Ruta", "Gestion Administrativa", "Otros"]
                            ubicacion_e = st.selectbox("¿Qué tipo de jornada?", opciones_jornada, index=opciones_jornada.index(ubicacion_def) if ubicacion_def in opciones_jornada else 0, key=f"ubicacion_e_{sufijo}")
                            
                            asesor_seleccionado_e = datos_originales.get("Asesor", "N/A")
                            zona_inspeccion_e = datos_originales.get("Zona", "N/A") if not pd.isna(datos_originales.get("Zona")) else ""
                            clientes_actuales_e = int(datos_originales.get("Clientes_Actuales", 25)) if not pd.isna(datos_originales.get("Clientes_Actuales")) else 25
                            clientes_a_captar_e = int(datos_originales.get("Clientes_Captar", 0)) if not pd.isna(datos_originales.get("Clientes_Actuales")) else 0
                            foco_dia_e = datos_originales.get("Objetivo_Principal", "") if not pd.isna(datos_originales.get("Objetivo_Principal")) else ""
                            
                            enf_guardados = datos_originales.get("Enfoque", "")
                            lista_enf_def = [e.strip() for e in enf_guardados.split(",")] if isinstance(enf_guardados, str) and enf_guardados.strip() != "" else []
                            
                            aud_jamon_def = bool(datos_originales.get("Auditoria_Jamones", False))
                            aud_queso_def = bool(datos_originales.get("Auditoria_Quesos", False))

                            monto_proyectado_e = float(datos_originales.get("Monto_Proyectado_Cobro", 0.0)) if not pd.isna(datos_originales.get("Monto_Proyectado_Cobro")) else 0.0
                            cajas_objetivo_e = int(datos_originales.get("Cajas_Objetivo", 0)) if not pd.isna(datos_originales.get("Cajas_Objetivo")) else 0
                            kilos_objetivo_e = float(datos_originales.get("Kilos_Objetivo", 0.0)) if not pd.isna(datos_originales.get("Kilos_Objetivo")) else 0.0

                            if ubicacion_e in ["Acompañamiento en Calle", "Auditoria de Ruta"]:
                                col_ae1, col_ae2 = st.columns(2)
                                with col_ae1:
                                    opciones_acomp = ["No", "Sí"]
                                    acompañado_e = st.radio(
                                        "¿Acompañamiento directo?", 
                                        opciones_acomp, 
                                        index=opciones_acomp.index(acompañado_e) if acompañado_e in opciones_acomp else 0, 
                                        key=f"acomp_e_{sufijo}"
                                    )
                                    if acompañado_e == "Sí":
                                        asesores_filtrados = tb_asesores[tb_asesores["ID_Usuario"].astype(str) == str(id_supervisor_activo)]["Nombre_Asesor"].tolist()
                                        if asesores_filtrados: 
                                            asesor_seleccionado_e = st.selectbox("Selecciona Asesor:", asesores_filtrados, index=asesores_filtrados.index(asesor_seleccionado_e) if asesor_seleccionado_e in asesores_filtrados else 0, key=f"ase_e_{sufijo}")
                                    else:
                                        asesor_seleccionado_e = "N/A"
                                    
                                    zona_inspeccion_e = st.text_input("📍 Zona de visita:", value=zona_inspeccion_e if zona_inspeccion_e != "N/A" else "", key=f"zona_e_{sufijo}")
                                
                                with col_ae2:
                                    clientes_actuales_e = st.number_input("Clientes en Ruta para Hoy:", min_value=0, value=clientes_actuales_e, step=1, key=f"clt_act_e_{sufijo}")
                                    
                                    if 0 < clientes_actuales_e < 25:
                                        falta_e = 25 - clientes_actuales_e
                                        clientes_a_captar_e = st.number_input("Clientes a captar hoy (Edición):", min_value=0, max_value=25, value=falta_e, key=f"clt_cap_e_{sufijo}")
                                    elif clientes_actuales_e >= 25:
                                        st.success("✅ ¡Ruta óptima!")
                                        clientes_a_captar_e = 0

                                st.markdown("### 🎯 Estrategia y Foco Comercial")
                                foco_dia_e = st.text_area("Objetivo Principal:", value=foco_dia_e, key=f"foco_e_{sufijo}")
                                
                                opciones_enfoque = ["Barrido(Captación)", "Desarrollo(Oportunidad)"]
                                valid_enf_defaults = [e for e in lista_enf_def if e in opciones_enfoque]
                                
                                enfoques_seleccionados_e = st.multiselect("Enfoque:", options=opciones_enfoque, default=valid_enf_defaults, key=f"enf_s_e_{sufijo}")
                                
                                st.markdown("#### 🏆 Auditoría de Concursos")
                                col_cone1, col_cone2 = st.columns(2)
                                auditar_concurso_a_e = col_cone1.checkbox("Auditar Concurso de Jamones", value=aud_jamon_def, key=f"aud_j_e_{sufijo}")
                                auditar_concurso_b_e = col_cone2.checkbox("Auditar Concurso de Quesos", value=aud_queso_def, key=f"aud_q_e_{sufijo}")
                                
                                st.markdown("### 📦 Proyección de Cuotas")
                                col_ve1, col_ve2, col_ve3 = st.columns(3)
                                monto_proyectado_e = col_ve1.number_input("Cobranza ($):", min_value=0.0, value=monto_proyectado_e, key=f"monto_e_{sufijo}")
                                cajas_objetivo_e = col_ve2.number_input("Meta Cajas:", min_value=0, value=cajas_objetivo_e, key=f"cajas_e_{sufijo}")
                                kilos_objetivo_e = col_ve3.number_input("Meta Kilos:", min_value=0.0, value=kilos_objetivo_e, key=f"kilos_e_{sufijo}")

                            elif ubicacion_e == "Gestion Administrativa":
                                st.markdown("### 🏢 Gestión Administrativa")
                                with st.container(border=True):
                                    st.write("**💰 Presupuesto de Recuperación**")
                                    monto_proyectado_e = st.number_input("Monto de Cobranza Vencida del Día ($):", min_value=0.0, value=monto_proyectado_e, key=f"monto_adm_e_{sufijo}")
                                
                                foco_dia_e = st.text_area("Detalle de la actividad administrativa:", value=foco_dia_e, key=f"foco_admin_e_{sufijo}")
                                
                                acompañado_e = "No"
                                asesor_seleccionado_e = "N/A"
                                zona_inspeccion_e = "N/A"

                            elif ubicacion_e == "Otros":
                                st.markdown("### 📝 Otras Actividades")
                                with st.container(border=True):
                                    st.write("**💰 Presupuesto de Recuperación**")
                                    monto_proyectado_e = st.number_input("Monto de Cobranza Vencida del Día ($):", min_value=0.0, value=monto_proyectado_e, key=f"monto_otr_e_{sufijo}")
                                
                                foco_dia_e = st.text_area("Detalle de la actividad:", value=foco_dia_e, key=f"foco_otros_e_{sufijo}")
                                
                                acompañado_e = "No"
                                asesor_seleccionado_e = "N/A"
                                zona_inspeccion_e = "N/A"

                            st.write("---")
                            
                            espacio_mensaje_abajo = st.empty()
                            
                            if "msg_exito_editar" in st.session_state:
                                espacio_mensaje_abajo.success(st.session_state["msg_exito_editar"])
                                del st.session_state["msg_exito_editar"]
                            
                            if st.button("🔄 Sobrescribir y Actualizar Planificación", use_container_width=True, key=f"btn_actualizar_existe_{sufijo}"):
                                 # Validar que no exista un cierre asociado antes de permitir la edición
                                 if has_linked_cierre(str(fecha_a_corregir), supervisor_nombre):
                                     st.error("⚠️ No es posible editar la planificación porque ya está asociado un cierre de resultados.")
                                     st.stop()
                                 str_enfoques_e = ",".join(enfoques_seleccionados_e) if 'enfoques_seleccionados_e' in locals() else ""
                                 
                                 nuevo_registro = {
                                     "Fecha": str(fecha_a_corregir), "Supervisor": supervisor_nombre, "Región": region_nombre, "Sucursal": suc_selec,
                                     "Modalidad": ubicacion_e, "Acompañamiento": acompañado_e, "Asesor": asesor_seleccionado_e,
                                     "Zona": zona_inspeccion_e, "Clientes_Actuales": int(clientes_actuales_e), "Clientes_Captar": int(clientes_a_captar_e),
                                     "Objetivo_Principal": foco_dia_e, "Enfoque": str_enfoques_e,
                                     "Auditoria_Jamones": 1 if auditar_concurso_a_e else 0, "Auditoria_Quesos": 1 if auditar_concurso_b_e else 0,
                                     "Monto_Proyectado_Cobro": monto_proyectado_e, "Cajas_Objetivo": cajas_objetivo_e, "Kilos_Objetivo": kilos_objetivo_e,
                                 }
                                 
                                 # Ejecutamos todo el guardado dentro de un spinner de carga para asegurar la persistencia
                                 with st.spinner("Guardando cambios y sincronizando base de datos..."):
                                     # Sincronización de cierre omitida en la edición de planificación
                                     
                                     # Filtramos y preparamos el nuevo DataFrame
                                     df_historico_plan = df_historico_plan[~((df_historico_plan["Supervisor"] == supervisor_nombre) & (df_historico_plan["Fecha"].astype(str) == str(fecha_a_corregir)))]
                                     df_final_actualizado = pd.concat([df_historico_plan, pd.DataFrame([nuevo_registro])], ignore_index=True)
                                     
                                     # Subida limpia a Django / Excel asegurando que termine antes del rerun
                                     actualizar_tabla_excel(df_final_actualizado, "Planificacion_Semanal", rerun=False)
                                     
                                     # Guardamos el mensaje de éxito en el session_state DESPUÉS de asegurar la subida
                                     st.session_state["msg_exito_editar"] = f"🔄 ¡Planificación del {fecha_a_corregir} modificada y guardada con éxito!"
                                     
                                     # Ahora sí, recargamos de forma segura para renderizar los nuevos datos
                                     st.rerun()