# src/views/dashboard.py
import streamlit as st

def show_dashboard():
    # =========================================================
    # ⚡ ENCAPSULAMIENTO DE LIBRERÍAS PESADAS (Optimización Global)
    # =========================================================
    import pandas as pd
    import plotly.express as px
    from src.database.queries import cargar_tabla_cached

    # Título estático inicial rápido
    st.title("📊 Panel de Indicadores Comerciales")
    st.markdown("<p style='color: #A0AAB2;'>Monitoreo en tiempo real de cuotas, coberturas y ejecución</p>", unsafe_allow_html=True)
    st.write("---")
    
    # Carga de datos mediante caché protegida
    df_mañana = cargar_tabla_cached("Planificacion_Semanal")
    df_tarde = cargar_tabla_cached("Resultados_Tarde")
    
    # Captura limpia de roles y usuario de la sesión
    rol_limpio = str(st.session_state.get("rol_actual", "")).lower().strip()
    usuario_conectado = str(st.session_state.get("usuario_actual", "")).strip()
    es_supervisor = (rol_limpio == "supervisor" or rol_limpio == "3")

    # =========================================================
    # 🛡️ FILTRADO ANTES DEL MERGE (Pre-Hardening de Seguridad)
    # =========================================================
    # Si es supervisor, limpiamos sus datos antes de cruzarlos para evitar fugas por cruce de tablas
    if es_supervisor and not df_tarde.empty:
        df_tarde["Supervisor_Clean"] = df_tarde["Supervisor"].astype(str).str.strip().str.lower()
        df_tarde = df_tarde[df_tarde["Supervisor_Clean"] == usuario_conectado.lower()].copy()
        df_tarde = df_tarde.drop(columns=["Supervisor_Clean"])

    if es_supervisor and not df_mañana.empty:
        df_mañana["Supervisor_Clean"] = df_mañana["Supervisor"].astype(str).str.strip().str.lower()
        df_mañana = df_mañana[df_mañana["Supervisor_Clean"] == usuario_conectado.lower()].copy()
        df_mañana = df_mañana.drop(columns=["Supervisor_Clean"])

    # Procesamiento y Cruce Seguro
    if not df_tarde.empty and not df_mañana.empty:
        df_mañana_join = df_mañana[["Fecha", "Supervisor", "Asesor", "Modalidad", "Acompañamiento", "Zona", "Objetivo_Principal"]].copy()
        df_mañana_join = df_mañana_join.rename(columns={"Fecha": "Fecha_Cierre"})
        
        # Limpieza estricta de llaves de cruce
        df_tarde["Fecha_Cierre"] = df_tarde["Fecha_Cierre"].astype(str).str.strip()
        df_mañana_join["Fecha_Cierre"] = df_mañana_join["Fecha_Cierre"].astype(str).str.strip()
        df_tarde["Supervisor"] = df_tarde["Supervisor"].astype(str).str.strip()
        df_mañana_join["Supervisor"] = df_mañana_join["Supervisor"].astype(str).str.strip()
        
        df_tarde_completo = df_tarde.merge(df_mañana_join, on=["Fecha_Cierre", "Supervisor"], how="left")
    else:
        df_tarde_completo = df_tarde.copy()
        
    if "Asesor" not in df_tarde_completo.columns:
        df_tarde_completo["Asesor"] = "Asesor sin nombre"

    # =========================================================
    # ⚙️ DEFINICIÓN DE ÁMBITOS VISUALES
    # =========================================================
    if not df_tarde_completo.empty:
        if es_supervisor:
            regiones_disp = [st.session_state.get("region_usuario", "")]
            sucursales_disp = [st.session_state.get("sucursal_usuario", "")]
            supervisores_disp = [usuario_conectado]
            
        elif rol_limpio == "coordinador" or rol_limpio == "2":
            region_coord = st.session_state.get("region_usuario", "")
            df_tarde_completo = df_tarde_completo[df_tarde_completo["Región"].astype(str).str.strip().str.lower() == str(region_coord).lower().strip()].copy()
            
            regiones_disp = [region_coord]
            sucursales_disp = df_tarde_completo["Sucursal"].dropna().unique().tolist()
            supervisores_disp = df_tarde_completo["Supervisor"].dropna().unique().tolist()
            
        else:  # Administrador / Master
            regiones_disp = df_tarde_completo["Región"].dropna().unique().tolist()
            sucursales_disp = df_tarde_completo["Sucursal"].dropna().unique().tolist()
            supervisores_disp = df_tarde_completo["Supervisor"].dropna().unique().tolist()

        # Bloque de Filtros Estilizado
        with st.container(border=True):
            col_f1, col_f2, col_f3, col_f4 = st.columns(4)
            
            with col_f1: 
                region_filtro = st.multiselect("📍 Región:", options=regiones_disp, default=regiones_disp, disabled=es_supervisor)
            with col_f2: 
                suc_opciones = df_tarde_completo[df_tarde_completo["Región"].isin(region_filtro)]["Sucursal"].dropna().unique().tolist()
                sucursal_filtro = st.selectbox("🏢 Sucursal:", options=suc_opciones, index=0 if suc_opciones else None, disabled=es_supervisor)
            with col_f3: 
                sup_opciones = df_tarde_completo[df_tarde_completo["Sucursal"] == sucursal_filtro]["Supervisor"].dropna().unique().tolist()
                supervisor_filtro = st.selectbox("👤 Supervisor:", options=sup_opciones, index=0 if sup_opciones else None, disabled=es_supervisor)
            with col_f4:
                fechas_disponibles_dash = sorted(df_tarde_completo["Fecha_Cierre"].dropna().unique(), reverse=True)
                fecha_filtro_sel = st.selectbox("📅 Fecha de Jornada:", ["Acumulado Histórico"] + list(fechas_disponibles_dash))

        # =========================================================
        # 🔒 FILTRADO FINAL DE SEGURIDAD ULTRA-ESTRICTO
        # =========================================================
        if es_supervisor:
            # Obligamos al sistema a buscar coincidencias ignorando mayúsculas/minúsculas y espacios
            df_dash = df_tarde_completo[df_tarde_completo["Supervisor"].astype(str).str.strip().str.lower() == usuario_conectado.lower()].copy()
        else:
            df_dash = df_tarde_completo[
                (df_tarde_completo["Región"].isin(region_filtro)) &
                (df_tarde_completo["Sucursal"] == sucursal_filtro) &
                (df_tarde_completo["Supervisor"] == supervisor_filtro)
            ].copy()

        if fecha_filtro_sel != "Acumulado Histórico":
            df_dash = df_dash[df_dash["Fecha_Cierre"] == str(fecha_filtro_sel)]

        # =========================================================
        # 🚀 RENDERIZADO DE TARJETAS Y KPIs
        # =========================================================
        if not df_dash.empty:
            total_cajas_plan = df_dash["Meta_Cajas_Matutina"].sum()
            total_cajas_real = df_dash["Cajas_Reales"].sum()
            total_cobranza_plan = df_dash["Meta_Cobranza_Matutina"].sum()
            total_cobranza_real = df_dash["Monto_Cobrado_Real"].sum()
            total_clientes_ruta = df_dash["Total_Clientes_Dia"].sum()
            total_clientes_act = df_dash["Clientes_Activados"].sum()
            total_aperturas = df_dash["Clientes_Apertura_Nuevos"].sum()

            cumplimiento_volumen = (total_cajas_real / total_cajas_plan * 100) if total_cajas_plan > 0 else 0.0
            cumplimiento_cobro = (total_cobranza_real / total_cobranza_plan * 100) if total_cobranza_plan > 0 else 0.0
            efectividad_activacion = (total_clientes_act / total_clientes_ruta * 100) if total_clientes_ruta > 0 else 0.0

            st.write("")
            k_col1, k_col2, k_col3, k_col4 = st.columns(4)
            
            # Ajuste de banderas individuales
            supervisores_en_dash = df_dash["Supervisor"].dropna().unique().tolist()
            es_reporte_individual = (len(supervisores_en_dash) == 1 and fecha_filtro_sel != "Acumulado Histórico")
            estado_acompañamiento = df_dash["Acompañamiento"].iloc[0] if "Acompañamiento" in df_dash.columns and es_reporte_individual else "Sí"
            fue_solo = (estado_acompañamiento == "No")

            titulo_efectividad = "Clientes Visitados" if fue_solo else "Efectividad de Ruta"
            subtitulo_efectividad = f"Visitados: {total_clientes_act} de {total_clientes_ruta}" if fue_solo else f"Efectivos: {total_clientes_act} / {total_clientes_ruta}"
            valor_efectividad = f"{efectividad_activacion:.1f}%" if not fue_solo else f"{total_clientes_act} Clts"

            with k_col1:
                st.markdown(f"""<div style="background: linear-gradient(135deg, #1e293b, #0f172a); padding: 20px; border-radius: 12px; border: 1px solid #334155; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
                    <p style="margin:0; font-size:12px; color:#94a3b8; font-weight:700; text-transform:uppercase; letter-spacing:0.5px;">📦 Volumen Total</p>
                    <h2 style="margin:8px 0 4px 0; color:#ffffff; font-size:28px; font-weight:800;">{total_cajas_real:,.0f} <span style="font-size:16px; font-weight:500; color:#cbd5e1;">Cjs</span></h2>
                    <span style="background-color:#1e3a8a; color:#60a5fa; font-size:11px; padding:2px 6px; border-radius:4px; font-weight:600;">Meta: {total_cajas_plan:,.0f} ({cumplimiento_volumen:.1f}%)</span>
                </div>""", unsafe_allow_html=True)

            with k_col2:
                st.markdown(f"""<div style="background: linear-gradient(135deg, #1e293b, #0f172a); padding: 20px; border-radius: 12px; border: 1px solid #334155; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
                    <p style="margin:0; font-size:12px; color:#94a3b8; font-weight:700; text-transform:uppercase; letter-spacing:0.5px;">💰 Cobranza Efectiva</p>
                    <h2 style="margin:8px 0 4px 0; color:#34d399; font-size:28px; font-weight:800;">${total_cobranza_real:,.2f}</h2>
                    <span style="background-color:#064e3b; color:#34d399; font-size:11px; padding:2px 6px; border-radius:4px; font-weight:600;">Meta: ${total_cobranza_plan:,.2f} ({cumplimiento_cobro:.1f}%)</span>
                </div>""", unsafe_allow_html=True)

            with k_col3:
                st.markdown(f"""<div style="background: linear-gradient(135deg, #1e293b, #0f172a); padding: 20px; border-radius: 12px; border: 1px solid #334155; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
                    <p style="margin:0; font-size:12px; color:#94a3b8; font-weight:700; text-transform:uppercase; letter-spacing:0.5px;">🎯 {titulo_efectividad}</p>
                    <h2 style="margin:8px 0 4px 0; color:#fbbf24; font-size:28px; font-weight:800;">{valor_efectividad}</h2>
                    <span style="background-color:#78350f; color:#fbbf24; font-size:11px; padding:2px 6px; border-radius:4px; font-weight:600;">{subtitulo_efectividad}</span>
                </div>""", unsafe_allow_html=True)

            with k_col4:
                st.markdown(f"""<div style="background: linear-gradient(135deg, #1e293b, #0f172a); padding: 20px; border-radius: 12px; border: 1px solid #334155; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
                    <p style="margin:0; font-size:12px; color:#94a3b8; font-weight:700; text-transform:uppercase; letter-spacing:0.5px;">🏆 Aperturas Nuevas</p>
                    <h2 style="margin:8px 0 4px 0; color:#f97316; font-size:28px; font-weight:800;">{total_aperturas} <span style="font-size:16px; font-weight:500; color:#cbd5e1;">Cód.</span></h2>
                    <span style="background-color:#7c2d12; color:#ffedd5; font-size:11px; padding:2px 6px; border-radius:4px; font-weight:600;">Nuevos Clientes</span>
                </div>""", unsafe_allow_html=True)

            st.write("")
            st.write("---")

            modalidades_en_df = df_dash["Modalidad"].dropna().unique() if "Modalidad" in df_dash.columns else []
            
            if es_reporte_individual and any(m in modalidades_en_df for m in ["Gestion Administrativa", "Otros"]):
                modalidad_actual = df_dash["Modalidad"].iloc[0]
                objetivo_del_dia = df_dash["Objetivo_Principal"].iloc[0] if "Objetivo_Principal" in df_dash.columns else "No especificado"
                
                st.markdown("### 🏢 Actividad Planificada de la Jornada")
                with st.chat_message("user", avatar="💼"):
                    st.markdown(f"#### **{modalidad_actual.upper()}**")
                    st.markdown(f"*{objetivo_del_dia}*")
                    st.caption(f"Registro archivado para la fecha: {fecha_filtro_sel} por el Supervisor Comercial.")
            
            else:
                st.markdown("### 🔍 Análisis de Penetración y Ejecución en el Punto de Venta")
                col_g1, col_g2 = st.columns(2)
                
                layout_premium = dict(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#cbd5e1', size=12), margin=dict(l=40, r=40, t=40, b=40),
                    xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(color='#94a3b8')),
                    yaxis=dict(showgrid=True, gridcolor='#334155', zeroline=False, tickfont=dict(color='#94a3b8'))
                )
                
                with col_g1:
                    with st.container(border=True):
                        st.markdown("<p style='font-weight:600; font-size:14px; margin-bottom:10px;'>🖼️ Cobertura de Material POP Real en Calle</p>", unsafe_allow_html=True)
                        total_pop_visitas = df_dash["Clts_Visita_Con_POP"].sum() if "Clts_Visita_Con_POP" in df_dash.columns else 0
                        pct_pop = (total_pop_visitas / total_clientes_act * 100) if total_clientes_act > 0 else 0.0
                        
                        df_chart_pop = pd.DataFrame([
                            {"Estado": "Con POP", "Clientes": total_pop_visitas}, 
                            {"Estado": "Sin POP", "Clientes": max(0, total_clientes_act - total_pop_visitas)}
                        ])
                        fig_pop = px.bar(df_chart_pop, x="Estado", y="Clientes", text_auto=True, color="Estado", color_discrete_map={"Con POP": "#10b981", "Sin POP": "#ef4444"})
                        fig_pop.update_layout(**layout_premium, showlegend=False, title=f"Efectividad Real: {pct_pop:.1f}%")
                        fig_pop.update_traces(textposition='outside', marker_line_width=0)
                        st.plotly_chart(fig_pop, use_container_width=True, config={'displayModeBar': False})

                with col_g2:
                    with st.container(border=True):
                        st.markdown("<p style='font-weight:600; font-size:14px; margin-bottom:10px;'>🛒 Distribución de Profundidad de Línea (Mix SKU)</p>", unsafe_allow_html=True)
                        s1 = df_dash["Clts_Con_1_SKU"].sum() if "Clts_Con_1_SKU" in df_dash.columns else 0
                        s2 = df_dash["Clts_Con_2_SKU"].sum() if "Clts_Con_2_SKU" in df_dash.columns else 0
                        s3 = df_dash["Clts_Con_Mas_3_SKU"].sum() if "Clts_Con_Mas_3_SKU" in df_dash.columns else 0
                        
                        df_chart_sku = pd.DataFrame([
                            {"Mix Portafolio": "1 SKU", "Clientes": s1}, 
                            {"Mix Portafolio": "2 SKUs", "Clientes": s2}, 
                            {"Mix Portafolio": "3+ SKUs", "Clientes": s3}
                        ])
                        fig_sku = px.bar(df_chart_sku, x="Mix Portafolio", y="Clientes", text_auto=True, color="Mix Portafolio", color_discrete_sequence=["#3b82f6", "#6366f1", "#8b5cf6"])
                        fig_sku.update_layout(**layout_premium, showlegend=False)
                        fig_sku.update_traces(textposition='outside', marker_line_width=0)
                        st.plotly_chart(fig_sku, use_container_width=True, config={'displayModeBar': False})

            # =========================================================
            # SECCIÓN SEPARADA: EVALUACIÓN Y AUDITORÍA DE CONCURSOS
            # =========================================================
            if es_reporte_individual and not any(m in modalidades_en_df for m in ["Gestion Administrativa", "Otros"]):
                row = df_dash.iloc[0]
                
                res_queso = row.get("Obs_Queso_Concurso", "")
                res_jamon = row.get("Obs_Jamon_Concurso", "")
                
                tiene_queso = pd.notna(res_queso) and str(res_queso).strip().lower() not in ["no", "n/a", "none", "nan", ""]
                tiene_jamon = pd.notna(res_jamon) and str(res_jamon).strip().lower() not in ["no", "n/a", "none", "nan", ""]
                tiene_concursos = tiene_queso or tiene_jamon
                
                if not fue_solo or tiene_concursos:
                    st.write("---")
                    nombre_asesor = row.get("Asesor", "Asesor sin nombre")
                    zona_planificada = row.get("Zona", "Zona no especificada")
                    objetivo_planificado = row.get("Objetivo_Principal", "Sin objetivo registrado")
                    nombre_supervisor = row.get("Supervisor", "Supervisor")
                
                    if fue_solo:
                        st.markdown(f"### 📋 Auditoría de Ruta: **Supervisor — {nombre_supervisor}**")
                    else:
                        st.markdown(f"### 📋 Evaluación y Auditoría: **{nombre_asesor}** — 📍 Ruta: *{zona_planificada}*")
                    
                    with st.container(border=True):
                        st.markdown(f"💡 **Objetivo Establecido en la Mañana:** *{objetivo_planificado}*")
                        
                        if not fue_solo:
                            st.markdown("<hr style='margin:12px 0; border-color:#334155;'>", unsafe_allow_html=True)
                            c1, c2, c3 = st.columns([1.5, 1.5, 2])
                            with c1:
                                st.caption("📋 Pasos de Visita")
                                st.markdown(f"**{row.get('Cumplio_Pasos_Visita', 'N/A')}**")
                            with c2:
                                st.caption("📖 Catálogo Digital")
                                st.markdown(f"**{row.get('Usa_Catalogo', 'N/A')}**")
                            with c3:
                                style_atencion = "<span style='color:#fbbf24; font-weight:700;'>"
                                st.caption("⭐️ Calidad de Atención")
                                st.markdown(f"{style_atencion}{row.get('Calidad_Atencion', 'N/A')}</span>", unsafe_allow_html=True)
                        
                        if tiene_concursos:
                            st.markdown("<hr style='margin:12px 0; border-color:#334155;'>", unsafe_allow_html=True)
                            st.markdown("🏆 **Auditoría de Concursos en el Punto de Venta:**")
                            
                            col_con1, col_con2 = st.columns(2)
                            with col_con1:
                                with st.container(border=True):
                                    st.markdown("<p style='font-size:13px; color:#94a3b8; font-weight:600; margin:0;'>🧀 Concurso Quesos</p>", unsafe_allow_html=True)
                                    if tiene_queso:
                                        st.write(res_queso)
                                    else:
                                        st.caption("Sin novedades registradas.")
                                        
                            with col_con2:
                                with st.container(border=True):
                                    st.markdown("<p style='font-size:13px; color:#94a3b8; font-weight:600; margin:0;'>🍖 Concurso Jamones</p>", unsafe_allow_html=True)
                                    if tiene_jamon:
                                        st.write(res_jamon)
                                    else:
                                        st.caption("Sin novedades registradas.")
                                        
        else:
            st.info("No se encontraron registros comerciales para los filtros seleccionados.")
    else:
        st.info("Aún no existen cierres de resultados en la base de datos.")