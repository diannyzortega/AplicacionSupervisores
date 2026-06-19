# src/views/resultados.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from src.database.queries import cargar_tabla_cached, actualizar_tabla_excel

def show_resultados():
    # Título estático inicial rápido
    st.title("🌙 Evaluación y Cierre de Resultados")
    st.markdown("<p style='color: #A0AAB2;'>Registro de Cierres de resultados de supervisores</p>", unsafe_allow_html=True)
    st.write("---")

    df_historico_cierres = cargar_tabla_cached("Resultados_Tarde")
    
    # Obtener rol actual
    rol = str(st.session_state.get("rol_actual", "asesor")).replace(".0", "").strip().lower()
    if rol == "1":
        rol = "administrador"
    elif rol == "2":
        rol = "coordinador"
    elif rol == "3":
        rol = "supervisor"

    if rol in ["administrador", "coordinador"]:
            if df_historico_cierres.empty:
                st.info("No hay cierres de resultados guardados en la base de datos.")
            else:
                if rol == "coordinador":
                    region_perfil = st.session_state["region_usuario"]
                    st.info(f"📋 Mostrando cierres diarios de la Región: **{region_perfil}**")
                    df_filtrado_cierres = df_historico_cierres[df_historico_cierres["Región"] == region_perfil].copy()
                else:
                    df_filtrado_cierres = df_historico_cierres.copy()
                    
                # --- BLOQUE DE FILTROS SUPERIORES INTERACTIVOS ---
                with st.container(border=True):
                    col_c1, col_c2, col_c3 = st.columns([1.5, 1.5, 2])
                    with col_c1:
                        fechas_disponibles_c = sorted(df_filtrado_cierres["Fecha_Cierre"].dropna().unique(), reverse=True)
                        fecha_sel_c = st.selectbox("Filtrar por Fecha de Cierre:", ["Todas las Fechas"] + list(fechas_disponibles_c), key="sb_fecha_c_cierre")
                    with col_c2:
                        if rol == "administrador":
                            regiones_disp_c = ["Todas"] + list(df_filtrado_cierres["Región"].dropna().unique())
                            reg_sel_c = st.selectbox("Filtrar por Región:", regiones_disp_c, key="sb_reg_cierre")
                            if reg_sel_c != "Todas":
                                df_filtrado_cierres = df_filtrado_cierres[df_filtrado_cierres["Región"] == reg_sel_c]
                        
                        sucursales_disp_c = ["Todas"] + list(df_filtrado_cierres["Sucursal"].dropna().unique())
                        suc_sel_c = st.selectbox("Filtrar por Sucursal:", sucursales_disp_c, key="sb_suc_cierre")
                        if suc_sel_c != "Todas":
                            df_filtrado_cierres = df_filtrado_cierres[df_filtrado_cierres["Sucursal"] == suc_sel_c]
                    with col_c3:
                        busqueda_c = st.text_input("🔍 Buscar por Supervisor:", placeholder="Ej: Jhon, Karla...", key="txt_bus_cierre")

                if fecha_sel_c != "Todas las Fechas":
                    df_filtrado_cierres = df_filtrado_cierres[df_filtrado_cierres["Fecha_Cierre"] == fecha_sel_c]
                if busqueda_c.strip() != "":
                    termino_c = busqueda_c.lower().strip()
                    df_filtrado_cierres = df_filtrado_cierres[df_filtrado_cierres["Supervisor"].astype(str).str.lower().str.contains(termino_c)]
                
                st.write("")
                st.markdown(f"**Registros encontrados:** `{len(df_filtrado_cierres)}`")
                
                # ⚡ CRUCE INTELIGENTE: Traemos de forma segura Asesor, Zona, Objetivo y Modalidad desde la mañana
                df_mañana_cruzar = cargar_tabla_cached("Planificacion_Semanal")
                if not df_mañana_cruzar.empty:
                    columnas_a_buscar = ["Fecha", "Supervisor"]
                    
                    if "Asesor" in df_mañana_cruzar.columns: 
                        columnas_a_buscar.append("Asesor")
                    if "Zona" in df_mañana_cruzar.columns: 
                        columnas_a_buscar.append("Zona")
                    if "Modalidad" in df_mañana_cruzar.columns:
                        columnas_a_buscar.append("Modalidad")
                    
                    columna_meta_real = None
                    for posible_nombre in ["Objetivo_Principal"]:
                        if posible_nombre in df_mañana_cruzar.columns:
                            columna_meta_real = posible_nombre
                            columnas_a_buscar.append(posible_nombre)
                            break
                    
                    df_mañana_join = df_mañana_cruzar[columnas_a_buscar].copy()
                    df_mañana_join = df_mañana_join.rename(columns={"Fecha": "Fecha_Cierre"})
                    
                    if columna_meta_real and columna_meta_real != "Objetivo":
                        df_mañana_join = df_mañana_join.rename(columns={columna_meta_real: "Objetivo"})
                    
                    # Limpieza preventiva para el merge
                    df_filtrado_cierres["Fecha_Cierre"] = df_filtrado_cierres["Fecha_Cierre"].astype(str).str.strip()
                    df_mañana_join["Fecha_Cierre"] = df_mañana_join["Fecha_Cierre"].astype(str).str.strip()
                    df_filtrado_cierres["Supervisor"] = df_filtrado_cierres["Supervisor"].astype(str).str.strip()
                    df_mañana_join["Supervisor"] = df_mañana_join["Supervisor"].astype(str).str.strip()
                    
                    # Fusionamos eliminando duplicados preventivos en la matriz matutina
                    df_mañana_join = df_mañana_join.drop_duplicates(subset=["Fecha_Cierre", "Supervisor"])
                    df_filtrado_cierres = df_filtrado_cierres.merge(df_mañana_join, on=["Fecha_Cierre", "Supervisor"], how="left")
                
                # Control por si no hay match matutino
                if "Asesor" not in df_filtrado_cierres.columns: df_filtrado_cierres["Asesor"] = "No especificado"
                if "Zona" not in df_filtrado_cierres.columns: df_filtrado_cierres["Zona"] = "No especificada"
                if "Objetivo" not in df_filtrado_cierres.columns: df_filtrado_cierres["Objetivo"] = "No especificado"
                if "Modalidad" not in df_filtrado_cierres.columns: df_filtrado_cierres["Modalidad"] = "Acompañamiento en Calle"

                # --- FUNCIÓN DISPARADORA DEL MODAL EMERGENTE PREMIUM ---
                @st.dialog("📊 Evaluación y Cierre de Resultados")
                def abrir_detalle_cierre(datos_fila):
                    import pandas as pd
                    modalidad = datos_fila.get('Modalidad', 'Acompañamiento en Calle')
                    
                    # Identificar si de forma matutina o por datos reales se detecta que fue una jornada de ruta sola
                    val_asesor = datos_fila.get('Asesor')
                    
                    es_campo = modalidad in ["Acompañamiento en Calle", "Auditoria de Ruta"]
                    
                    # 🛡️ Blindaje anti-NaN para el Asesor Comercial en el Cierre
                    # Detect if there is no advisor (blank, NaN, N/A, etc.)
                    fue_solo = pd.isna(val_asesor) or str(val_asesor).strip().lower() in ["nan", "", "none", "n/a", "na", "no especificado"]
                    if fue_solo:
                        nombre_asesor_mostrar = "No hubo acompañamiento (Gestión Solo)"
                    else:
                        nombre_asesor_mostrar = str(val_asesor).strip()

                    # Header: show Cierre de Asesor only when we have a real advisor
                    if es_campo and not fue_solo:
                        st.markdown(f"### Cierre de Asesor: **{nombre_asesor_mostrar}**")
                    else:
                        st.markdown(f"### Actividad Evaluada: **{modalidad}**")
                        
                    st.caption(f"Cerrado por: {datos_fila.get('Supervisor', 'N/A')} | Sucursal: {datos_fila.get('Sucursal', 'N/A')} | Fecha: {datos_fila.get('Fecha_Cierre', 'N/A')}")
                    st.write("---")

                    # --- COMPARATIVAS DE VOLUMEN Y FINANZAS (Kpis en Línea) ---
                    st.markdown("##### 📈 Desempeño Operativo vs Planificación Matutina")
                    k_col1, k_col2, k_col3 = st.columns(3)
                    
                    # Tarjeta 1: Cajas
                    cajas_m = float(datos_fila.get('Meta_Cajas_Matutina', 0.0)) if pd.notna(datos_fila.get('Meta_Cajas_Matutina')) else 0.0
                    cajas_r = float(datos_fila.get('Cajas_Reales', 0.0)) if pd.notna(datos_fila.get('Cajas_Reales')) else 0.0
                    color_cj = "#34d399" if cajas_r >= cajas_m and cajas_m > 0 else "#f87171" if cajas_m > 0 else "#ffffff"
                    with k_col1:
                        st.markdown(f"""<div style="background-color:#1e293b; padding:10px; border-radius:8px; border:1px solid #334155; text-align:center;">
                            <span style="font-size:11px; color:#94a3b8; font-weight:600;">VOLUMEN (CAJAS)</span>
                            <p style="margin:4px 0 0 0; font-size:13px; color:#94a3b8;">Meta: {cajas_m:,.0f} Cjs</p>
                            <h4 style="margin:2px 0 0 0; color:{color_cj};">{cajas_r:,.0f} Cjs Real</h4>
                        </div>""", unsafe_allow_html=True)

                    # Tarjeta 2: Kilos
                    kilos_m = float(datos_fila.get('Meta_Kilos_Matutina', 0.0)) if pd.notna(datos_fila.get('Meta_Kilos_Matutina')) else 0.0
                    kilos_r = float(datos_fila.get('Kilos_Reales', 0.0)) if pd.notna(datos_fila.get('Kilos_Reales')) else 0.0
                    color_kg = "#34d399" if kilos_r >= kilos_m and kilos_m > 0 else "#f87171" if kilos_m > 0 else "#ffffff"
                    with k_col2:
                        st.markdown(f"""<div style="background-color:#1e293b; padding:10px; border-radius:8px; border:1px solid #334155; text-align:center;">
                            <span style="font-size:11px; color:#94a3b8; font-weight:600;">MÁXIMO EN KILOS</span>
                            <p style="margin:4px 0 0 0; font-size:13px; color:#94a3b8;">Meta: {kilos_m:,.1f} Kg</p>
                            <h4 style="margin:2px 0 0 0; color:{color_kg};">{kilos_r:,.1f} Kg Real</h4>
                        </div>""", unsafe_allow_html=True)

                    # Tarjeta 3: Cobranza
                    cobro_m = float(datos_fila.get('Meta_Cobranza_Matutina', 0.0)) if pd.notna(datos_fila.get('Meta_Cobranza_Matutina')) else 0.0
                    cobro_r = float(datos_fila.get('Monto_Cobrado_Real', 0.0)) if pd.notna(datos_fila.get('Monto_Cobrado_Real')) else 0.0
                    color_cb = "#34d399" if cobro_r >= cobro_m and cobro_m > 0 else "#f87171" if cobro_m > 0 else "#34d399"
                    with k_col3:
                        st.markdown(f"""<div style="background-color:#1e293b; padding:10px; border-radius:8px; border:1px solid #334155; text-align:center;">
                            <span style="font-size:11px; color:#34d399; font-weight:600;">RECUPERACIÓN ($)</span>
                            <p style="margin:4px 0 0 0; font-size:13px; color:#94a3b8;">Meta: ${cobro_m:,.2f}</p>
                            <h4 style="margin:2px 0 0 0; color:{color_cb};">${cobro_r:,.2f} Real</h4>
                        </div>""", unsafe_allow_html=True)

                    st.write("")
                    
                    # --- BLOQUE LOGÍSTICO (Clientes de la Ruta) ---
                    if es_campo or int(datos_fila.get('Total_Clientes_Dia', 0)) > 0:
                        st.markdown("##### 📍 Logística de Cobertura y Efectividad")
                        ce1, ce2 = st.columns(2)
                        with ce1:
                            st.markdown(f"**🗺️ Zona / Ruta Asignada:** {datos_fila.get('Zona', 'N/A')}")
                            st.markdown(f"**👥 Universo Maestro de Ruta:** {int(datos_fila.get('Total_Clientes_Dia', 0))} Clientes")
                            st.markdown(f"**🎯 Clientes Activados Efectivos:** {int(datos_fila.get('Clientes_Activados', 0))}")
                        with ce2:
                            st.markdown(f"**🚀 Cuota de Captación Matutina:** {int(datos_fila.get('Clts_a_Captar', 0))} Clts")
                            st.markdown(f"**🆕 Nuevas Aperturas Reales:** {int(datos_fila.get('Clientes_Apertura_Nuevos', 0))}")
                            
                            clts_totales = int(datos_fila.get('Total_Clientes_Dia', 0))
                            efectividad = (int(datos_fila.get('Clientes_Activados', 0)) / clts_totales * 100) if clts_totales > 0 else 0.0
                            st.markdown(f"**📈 Efectividad de Compra:** `{efectividad:.1f}%` de la ruta")

                    # 🔍 VALIDACIÓN DE EVALUACIÓN OPERATIVA (Solo si NO fue solo)
                    raw_calidad = datos_fila.get('Calidad_Atencion')
                    # Determine if evaluation data is present and valid
                    tiene_evaluacion = pd.notna(raw_calidad) and str(raw_calidad).strip().lower() not in ["nan", "", "none", "n/a", "no especificado"]
                    usa_cat = datos_fila.get('Usa_Catalogo', 'N/A')
                    sigue_pasos = datos_fila.get('Cumplio_Pasos_Visita', 'N/A')
                    tiene_uso = usa_cat not in ["N/A", "No Especificado", "nan", "none", ""]
                    tiene_pasos = sigue_pasos not in ["N/A", "No Especificado", "nan", "none", ""]
                    if tiene_evaluacion and not fue_solo and tiene_uso and tiene_pasos:
                        st.write("")
                        st.markdown("##### 📋 Evaluación de Desempeño y Calidad de Visita")
                        with st.container(border=True):
                            ev1, ev2, ev3 = st.columns(3)
                            
                            with ev1:
                                usa_cat = datos_fila.get('Usa_Catalogo', 'No Especificado')
                                icon_cat = "✅" if usa_cat in ["Sí", "Completo", "Si"] else "❌" if usa_cat in ["No", "Incompleto"] else "⚠️"
                                st.markdown(f"**📖 Uso del Catálogo**\n<p style='font-size:15px;'>{icon_cat} {usa_cat}</p>", unsafe_allow_html=True)
                            
                            with ev2:
                                sigue_pasos = datos_fila.get('Cumplio_Pasos_Visita', 'No Especificado')
                                icon_pasos = "👣" if sigue_pasos in ["Sí", "Completo", "Si"] else "⚠️"
                                st.markdown(f"**🪜 Pasos de la Visita**\n<p style='font-size:15px;'>{icon_pasos} {sigue_pasos}</p>", unsafe_allow_html=True)

                            with ev3:
                                calidad_serv = str(raw_calidad).strip()
                                icon_serv = "⭐" if "Excelente" in calidad_serv or "Buena" in calidad_serv else "👤"
                                st.markdown(f"**🌟 Calidad de Servicio**\n<p style='font-size:15px;'>{icon_serv} {calidad_serv}</p>", unsafe_allow_html=True)

                    # 🧀 EXTRAER AUDITORÍAS DE CONCURSOS COMPLETAMENTE LIBERADO DE CONDICIONES DE ACOMPAÑAMIENTO
                    obs_jamon = datos_fila.get('Obs_Jamon_Concurso', '')
                    obs_queso = datos_fila.get('Obs_Queso_Concurso', '')
                    
                    tiene_jamon = pd.notna(obs_jamon) and str(obs_jamon).strip().lower() not in ["nan", "none", "", "no", "n/a"]
                    tiene_queso = pd.notna(obs_queso) and str(obs_queso).strip().lower() not in ["nan", "none", "", "no", "n/a"]
                    tiene_concursos = tiene_jamon or tiene_queso

                    if tiene_concursos:
                        st.write("")
                        st.markdown("##### 🏆 Estado de Concursos y Enfoques de Foco")
                        with st.container(border=True):
                            if tiene_jamon:
                                st.markdown(f"**🍖 Auditoría Concurso Jamones:** {str(obs_jamon).strip()}")
                            if tiene_queso:
                                st.markdown(f"**🧀 Auditoría Concurso Quesos:** {str(obs_queso).strip()}")

                    # --- ANÁLISIS DE MERCADO / OBSERVACIONES GENERALES ---
                    st.write("")
                    st.markdown("##### 📝 Novedades de Campo y Observaciones del Mercado")
                    with st.container(border=True):
                        st.markdown(f"**🎯 Objetivo:**")
                        st.markdown(f"*{datos_fila.get('Objetivo', 'No cruzado.')}*")
                        st.markdown("---")
                        st.markdown(f"**👁️ Resultados:**")
                        st.markdown(f"*{datos_fila.get('Novedades_Market', 'Sin novedades adicionales reportadas.')}*")

                    st.write("")
                    if st.button("Entendido / Cerrar", use_container_width=True, key="btn_close_modal_cierre"):
                        st.rerun()

                # --- CONSTRUCCIÓN DE LA TABLA MATRIZ COMPACTA PREMIUM ---
                st.markdown("""
                    <div style="background-color: #1e293b; padding: 10px 16px; border-radius: 8px 8px 0px 0px; border: 1px solid #334155; margin-bottom: 4px;">
                        <div style="display: flex; font-weight: bold; color: #cbd5e1; font-size: 14px;">
                            <div style="flex: 1.2;">📅 Fecha Cierre</div>
                            <div style="flex: 2;">👤 Supervisor</div>
                            <div style="flex: 1.5;">🏢 Sucursal</div>
                            <div style="flex: 3.5;">🏃 Tipo de Jornada Ejecutada</div>
                            <div style="flex: 2;">📰 Resultados</div>
                            <div style="flex: 1.3; text-align: center;">📊 Acción</div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                for idx, fila in df_filtrado_cierres.reset_index(drop=True).iterrows():
                    with st.container():
                        col1, col2, col3, col4, col5, col6 = st.columns([1.2, 2, 1.5, 3.5, 2, 1.3])
                        
                        with col1:
                            st.markdown(f"<p style='margin-top:6px; font-size:14px;'>{fila.get('Fecha_Cierre', 'N/A')}</p>", unsafe_allow_html=True)
                            
                        with col2:
                            st.markdown(f"<p style='margin-top:6px; font-size:14px; font-weight:600;'>{fila.get('Supervisor', 'N/A')}</p>", unsafe_allow_html=True)
                            
                        with col3:
                            st.markdown(f"<p style='margin-top:6px; font-size:14px; color:#94a3b8;'>{fila.get('Sucursal', 'N/A')}</p>", unsafe_allow_html=True)
                            
                        with col4:
                            modalidad_texto = fila.get('Modalidad', 'Acompañamiento en Calle')
                            if modalidad_texto in ["Acompañamiento en Calle", "Auditoria de Ruta"]:
                                color_badge = "#38bdf8"
                            elif modalidad_texto == "Gestion Administrativa":
                                color_badge = "#fbbf24"
                            else:
                                color_badge = "#a78bfa"
                            st.markdown(f"<p style='margin-top:6px; font-size:13px; font-weight:500; color:{color_badge};'>{modalidad_texto}</p>", unsafe_allow_html=True)
                            
                        with col5:
                            st.markdown(f"<p style='margin-top:6px; font-size:13px; color:#94a3b8;'>{fila.get('Novedades_Market', 'Sin novedades')}</p>", unsafe_allow_html=True)
                            
                        with col6:
                            if st.button("Ver Cierre", key=f"btn_mon_cierr_{idx}", use_container_width=True):
                                abrir_detalle_cierre(fila)
                                
                        st.markdown("<hr style='margin:4px 0; border-color:#1e293b;'>", unsafe_allow_html=True)

    elif rol == "supervisor":            
            df_historico_plan = cargar_tabla_cached("Planificacion_Semanal")
            
            suc_selec = st.session_state["sucursal_usuario"]
            region_nombre = st.session_state["region_usuario"]
            supervisor_nombre = st.session_state["usuario_actual"]
            
            fecha_cierre = st.date_input("Seleccione la fecha del día que está evaluando:", value=datetime.now().date(), key="fecha_cierre_val")
            
            sufijo_tarde = str(fecha_cierre)
            
            meta_cajas, meta_kilos, meta_cobranza = 0, 0.0, 0.0
            clts_ruta, clts_captar = 0, 0
            modalidad_matutina = ""
            acompañamiento_matutino = "No"
            plan_encontrado = False
            plan_audito_jamon = False
            plan_audito_queso = False
            
            if not df_historico_plan.empty:
                match_plan = df_historico_plan[(df_historico_plan["Supervisor"] == supervisor_nombre) & (df_historico_plan["Fecha"].astype(str) == str(fecha_cierre))]
                if not match_plan.empty:
                    plan_encontrado = True
                    row_plan = match_plan.iloc[0]
                    modalidad_matutina = row_plan.get("Modalidad", "Acompañamiento en Calle")
                    acompañamiento_matutino = row_plan.get("Acompañamiento", "No")
                    meta_cajas = int(row_plan.get("Cajas_Objetivo", 0)) if not pd.isna(row_plan.get("Cajas_Objetivo")) else 0
                    meta_kilos = float(row_plan.get("Kilos_Objetivo", 0.0)) if not pd.isna(row_plan.get("Kilos_Objetivo")) else 0.0
                    meta_cobranza = float(row_plan.get("Monto_Proyectado_Cobro", 0.0)) if not pd.isna(row_plan.get("Monto_Proyectado_Cobro")) else 0.0
                    clts_ruta = int(row_plan.get("Clientes_Actuales", 0)) if not pd.isna(row_plan.get("Clientes_Actuales")) else 0
                    clts_captar = int(row_plan.get("Clientes_Captar", 0)) if not pd.isna(row_plan.get("Clientes_Captar")) else 0
                    
                    def evaluar_booleano(val):
                        if pd.isna(val): return False
                        if isinstance(val, str):
                            return val.strip().lower() in ["sí", "si", "true", "1", "verdadero"]
                        if isinstance(val, (int, float)): return int(val) == 1
                        return bool(val)

                    plan_audito_jamon = evaluar_booleano(row_plan.get("Auditoria_Jamones", False))
                    plan_audito_queso = evaluar_booleano(row_plan.get("Auditoria_Quesos", False))

            if not plan_encontrado:
                st.error(f"❌ **No se puede cargar el cierre:** No has registrado una planificación matutina para la fecha **{fecha_cierre}**.")
                st.info("💡 Por favor, ve primero a la opción de **Planificación Matutina**, registra tu jornada de la mañana para este día y luego regresa aquí para evaluar tus resultados.")
            
            else:
                modo_edicion_cierre = False
                datos_cierre_guardado = {}
                if not df_historico_cierres.empty:
                    cierre_existente = df_historico_cierres[
                        (df_historico_cierres["Supervisor"] == supervisor_nombre) & 
                        (df_historico_cierres["Fecha_Cierre"].astype(str) == str(fecha_cierre))
                    ]
                    if not cierre_existente.empty:
                        modo_edicion_cierre = True
                        datos_cierre_guardado = cierre_existente.iloc[0].to_dict()
                        st.warning(f"📝 **Nota:** Ya registraste un cierre para el {fecha_cierre}. Rellena los campos para modificar y sobrescribir el reporte anterior.")

                if modalidad_matutina in ["Gestion Administrativa", "Otros"]:
                    st.success(f"🏢 Planificación de Oficina detectada (**{modalidad_matutina}**). Meta de Recuperación Financiera: **${meta_cobranza:,.2f}**.")
                else:
                    st.success(
                        f"🏃 **Planificación de Calle detectada** (Modalidad: *{modalidad_matutina}*)\n\n"
                        f"🎯 **Metas establecidas para la jornada:**\n"
                        f"* 📦 **Cajas:** {meta_cajas} Cjs\n"
                        f"* ⚖️ **Kilos:** {meta_kilos:,.2f} Kg\n"
                        f"* 💰 **Cobranza:** ${meta_cobranza:,.2f}\n"
                        f"* 🗺️ **Cartera Asignada:** {clts_ruta} Clientes en Ruta"
                    )

                def_cajas = int(datos_cierre_guardado.get("Cajas_Reales", 0)) if modo_edicion_cierre else 0
                def_kilos = float(datos_cierre_guardado.get("Kilos_Reales", 0.0)) if modo_edicion_cierre else 0.0
                def_monto = float(datos_cierre_guardado.get("Monto_Cobrado_Real", 0.0)) if modo_edicion_cierre else 0.0
                def_act = int(datos_cierre_guardado.get("Clientes_Activados", 0)) if modo_edicion_cierre else 0
                def_ape = int(datos_cierre_guardado.get("Clientes_Apertura_Nuevos", 0)) if modo_edicion_cierre else 0
                def_pop = int(datos_cierre_guardado.get("Clts_Visita_Con_POP", 0)) if modo_edicion_cierre else 0
                
                def_1sku = int(datos_cierre_guardado.get("Clts_Con_1_SKU", 0)) if modo_edicion_cierre else 0
                def_2sku = int(datos_cierre_guardado.get("Clts_Con_2_SKU", 0)) if modo_edicion_cierre else 0
                def_3sku = int(datos_cierre_guardado.get("Clts_Con_Mas_3_SKU", 0)) if modo_edicion_cierre else 0
                
                def_pasos = datos_cierre_guardado.get("Cumplio_Pasos_Visita", "Sí") if modo_edicion_cierre else "Sí"
                def_catalogo = datos_cierre_guardado.get("Usa_Catalogo", "Sí") if modo_edicion_cierre else "Sí"
                def_atencion = datos_cierre_guardado.get("Calidad_Atencion", "Buena") if modo_edicion_cierre else "Buena"
                
                def_obs_jamon = str(datos_cierre_guardado.get("Obs_Jamon_Concurso", "")) if modo_edicion_cierre else ""
                def_obs_queso = str(datos_cierre_guardado.get("Obs_Queso_Concurso", "")) if modo_edicion_cierre else ""
                def_cumplio = datos_cierre_guardado.get("Cumplimiento_Plan", "Sí") if modo_edicion_cierre else "Sí"
                def_nov = datos_cierre_guardado.get("Novedades_Market", "") if modo_edicion_cierre else ""

                cajas_reales, kilos_reales, monto_cobrado = 0, 0.0, 0.0
                clientes_activados, clientes_apertura, c_pop = 0, 0, 0
                c_1sku, c_2sku, c_3sku = 0, 0, 0
                cumple_pasos, usa_catalogo, calidad_atencion = "N/A", "N/A", "N/A"
                obs_jamon, obs_queso = "", ""

                if modalidad_matutina in ["Gestion Administrativa", "Otros"]:
                    st.markdown(f"#### 🏢 Cierre de Gestión: {modalidad_matutina}")
                    with st.container(border=True):
                        col_adm1, col_adm2 = st.columns([1, 2])
                        with col_adm1:
                            st.write("**💰 Control Financiero**")
                            monto_cobrado = st.number_input("Monto Recaudado / Gestión de Cobros ($):", min_value=0.0, value=def_monto, key=f"mnt_adm_{sufijo_tarde}")
                        with col_adm2:
                            st.write("**📝 Minuta de Resultados**")
                            novedades = st.text_area("Redacte detalladamente los resultados y avances de la jornada:", value=def_nov, placeholder="Ej: Se ejecutaron llamadas de cobro...", key=f"nov_adm_{sufijo_tarde}")
                    
                    opciones_cumplio_adm = ["Sí", "No", "Parcialmente"]
                    cumplio_plan = st.radio("¿Se cumplieron las actividades planificadas para hoy?", opciones_cumplio_adm, index=opciones_cumplio_adm.index(def_cumplio) if def_cumplio in opciones_cumplio_adm else 0, key=f"cumpl_adm_{sufijo_tarde}")

                else:
                    st.markdown("#### 📊 Desempeño Operativo y Comercial Real")
                    with st.container(border=True):
                        col_c1, col_c2, col_c3 = st.columns(3)
                        with col_c1:
                            st.write("**📦 1. KPI Volumen de Ventas**")
                            cajas_reales = st.number_input("Cajas Totales Logradas:", min_value=0, step=1, value=def_cajas, key=f"cj_r_{sufijo_tarde}")
                            kilos_reales = st.number_input("Kilos Totales Logrados (Kg):", min_value=0.0, value=def_kilos, key=f"kg_r_{sufijo_tarde}")
                        with col_c2:
                            st.write("**💰 2. KPI Cobranza**")
                            monto_cobrado = st.number_input("Monto Recaudado Hoy ($):", min_value=0.0, value=def_monto, key=f"mnt_r_{sufijo_tarde}")
                        with col_c3:
                            st.write("**🏃 3. KPI Activation y Apertura**")
                            
                            if acompañamiento_matutino == "No":
                                etiqueta_clientes = "Clientes Visitados:"
                            else:
                                etiqueta_clientes = "Clientes Activos (Compraron hoy):"
                                
                            clientes_activados = st.number_input(etiqueta_clientes, min_value=0, step=1, value=def_act, key=f"cl_act_r_{sufijo_tarde}")
                            clientes_apertura = st.number_input("Apertura de Nuevos Clientes (Códigos):", min_value=0, step=1, value=def_ape, key=f"cl_ap_r_{sufijo_tarde}")
                                    
                    st.markdown("#### 🔍 Auditoría Cuantitativa de Campo")
                    with st.container(border=True):
                        col_aud1, col_aud2 = st.columns(2)
                        
                        with col_aud1:
                            st.write("**🛒 4. Penetración de SKU (Profundidad)**")
                            st.caption(f"Distribuye los {clientes_activados} clientes según la variedad que se evidenció:")
                            c_1sku = st.number_input("¿Cuántos clientes evidenciaron solo 1 SKU?", min_value=0, step=1, value=def_1sku, key=f"sku1_{sufijo_tarde}")
                            c_2sku = st.number_input("¿Cuántos clientes evidenciaron exactamente 2 SKUs?", min_value=0, step=1, value=def_2sku, key=f"sku2_{sufijo_tarde}")
                            c_3sku = st.number_input("¿Cuántos clientes evidenciaron 3 o más SKUs?", min_value=0, step=1, value=def_3sku, key=f"sku3_{sufijo_tarde}")
                            
                            suma_skus = c_1sku + c_2sku + c_3sku
                            if suma_skus != clientes_activados:
                                st.error(f"❌ La suma de clientes por SKU ({suma_skus}) no coincide con el total ingresado arriba ({clientes_activados}).")
                            else:
                                st.success("✅ Distribución del Mix de SKUs correcta.")

                        with col_aud2:
                            st.write("**🖼️ 5. Auditoría de Trade Marketing (POP)**")
                            c_pop = st.number_input("¿En cuántos de los clientes visitados se evidenció material POP?", min_value=0, max_value=int(max(0, clts_ruta)), step=1, value=def_pop, key=f"pop_cuant_{sufijo_tarde}")
                            
                            if acompañamiento_matutino == "Sí":
                                st.write("**👤 6. Parámetros de Ruta**")
                                opciones_sn = ["Sí", "No"]
                                opciones_calidad = ["Excelente", "Buena", "Regular", "Deficiente"]
                                
                                cumple_pasos = st.radio("¿El asesor cumple con todos los pasos de la visita de forma consistente?", opciones_sn, index=opciones_sn.index(def_pasos) if def_pasos in opciones_sn else 0, horizontal=True, key=f"pas_r_{sufijo_tarde}")
                                usa_catalogo = st.radio("¿El asesor utilizó el catálogo digital durante la venta?", opciones_sn, index=opciones_sn.index(def_catalogo) if def_catalogo in opciones_sn else 0, horizontal=True, key=f"cat_r_{sufijo_tarde}")
                                calidad_atencion = st.selectbox("¿Cómo fue la calidad de atención del asesor con el cliente?", opciones_calidad, index=opciones_calidad.index(def_atencion) if def_atencion in opciones_calidad else 1, key=f"atn_r_{sufijo_tarde}")
                            else:
                                cumple_pasos, usa_catalogo, calidad_atencion = "N/A", "N/A", "N/A"
                                st.info("ℹ️ Parámetros de asesor omitidos: Jornada individual sin supervisión de personal.")

                    if plan_audito_jamon or plan_audito_queso:
                        st.markdown("#### 🏆 7. Resultados de Auditoría de Concursos")
                        with st.container(border=True):
                            st.info("📝 Redacta las novedades, marcas, stock o precios detectados en la calle:")
                            num_columnas = (1 if plan_audito_jamon else 0) + (1 if plan_audito_queso else 0)
                            cols_concursos = st.columns(num_columnas)
                            
                            idx_col = 0
                            if plan_audito_jamon:
                                with cols_concursos[idx_col]:
                                    obs_jamon = st.text_input("Resultados Auditoria Concurso de Jamón:", value=def_obs_jamon, placeholder="Ej: Halladas 3 piezas de marca X, inventario alto...", key=f"txt_jam_c_{sufijo_tarde}")
                                idx_col += 1
                                
                            if plan_audito_queso:
                                with cols_concursos[idx_col]:
                                    obs_queso = st.text_input("Resultados Auditoria Concurso de Queso:", value=def_obs_queso, placeholder="Ej: Precio competitivo, fuerte presencia de marca Y...", key=f"txt_que_c_{sufijo_tarde}")
                                    
                    st.write("---")
                    opciones_cumplio_r = ["Sí", "No", "Parcialmente"]
                    cumplio_plan = st.radio("¿Se cumplió la planificación estratégica del día?", opciones_cumplio_r, index=opciones_cumplio_r.index(def_cumplio) if def_cumplio in opciones_cumplio_r else 0, key=f"cumpl_r_{sufijo_tarde}")
                    novedades = st.text_area("Novedades del Mercado / Comentarios de Ruta:", value=def_nov, key=f"nov_r_{sufijo_tarde}")
                
                st.write("---")
                etiqueta_boton = "🔄 Sobrescribir y Actualizar Cierre" if modo_edicion_cierre else "💾 Guardar Resultados del Día"
                
                if st.button(etiqueta_boton, use_container_width=True, key=f"btn_save_cierre_{sufijo_tarde}"):
                    if modalidad_matutina not in ["Gestion Administrativa", "Otros"] and (c_1sku + c_2sku + c_3sku) != clientes_activados:
                        st.error("❌ No se pueden guardar los datos. Corrija la distribución de SKUs para que coincida con el total ingresado.")
                    elif modalidad_matutina in ["Gestion Administrativa", "Otros"] and novedades.strip() == "":
                        st.error("❌ Por favor, redacte la minuta de los resultados o gestiones realizadas antes de guardar.")
                    else:
                        registro_tarde = {
                            "Fecha_Cierre": str(fecha_cierre), "Supervisor": supervisor_nombre, "Región": region_nombre, "Sucursal": suc_selec,
                            "Total_Clientes_Dia": int(clts_ruta), "Clts_a_Captar": int(clts_captar),
                            "Meta_Cajas_Matutina": meta_cajas, "Meta_Kilos_Matutina": meta_kilos, "Meta_Cobranza_Matutina": meta_cobranza,
                            "Cajas_Reales": int(cajas_reales), "Kilos_Reales": float(kilos_reales), "Monto_Cobrado_Real": float(monto_cobrado), 
                            "Clientes_Activados": int(clientes_activados), "Clientes_Apertura_Nuevos": int(clientes_apertura), 
                            "Clts_Visita_Con_POP": int(c_pop), "Clts_Con_1_SKU": int(c_1sku), "Clts_Con_2_SKU": int(c_2sku), "Clts_Con_Mas_3_SKU": int(c_3sku),
                            "Cumplio_Pasos_Visita": cumple_pasos, "Usa_Catalogo": usa_catalogo, "Calidad_Atencion": calidad_atencion, 
                            "Audito_Jamon": "Sí" if plan_audito_jamon else "No", "Obs_Jamon_Concurso": str(obs_jamon),
                            "Audito_Queso": "Sí" if plan_audito_queso else "No", "Obs_Queso_Concurso": str(obs_queso),
                            "Cumplimiento_Plan": cumplio_plan, "Novedades_Market": novedades
                        }
                        
                        if modo_edicion_cierre:
                            df_historico_cierres = df_historico_cierres[~((df_historico_cierres["Supervisor"] == supervisor_nombre) & (df_historico_cierres["Fecha_Cierre"].astype(str) == str(fecha_cierre)))]
                        
                        df_final_cierre = pd.concat([df_historico_cierres, pd.DataFrame([registro_tarde])], ignore_index=True)
                        
                        if modo_edicion_cierre:
                            st.session_state["msg_exito_cierre"] = f"🔄 ¡El cierre de resultados del {fecha_cierre} ha sido sobrescrito y actualizado con éxito!"
                        else:
                            st.session_state["msg_exito_cierre"] = f"🌙 ¡Cierre Guardado con éxito para el {str(fecha_cierre)} bajo la modalidad {modalidad_matutina}!"
                            
                        actualizar_tabla_excel(df_final_cierre, "Resultados_Tarde")


                if "msg_exito_cierre" in st.session_state:
                    st.success(st.session_state["msg_exito_cierre"])
                    del st.session_state["msg_exito_cierre"]       