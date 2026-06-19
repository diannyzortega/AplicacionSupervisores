# src/views/seguimiento.py
import streamlit as st
import pandas as pd

def show_seguimiento():
    from comercial.models import Asesor, Categoria, AsesorCategoria, UserProfile, SeguimientoDiario

    st.title("📈 Seguimiento Asesores")
    st.markdown("<p style='color: #A0AAB2;'>Monitoreo en tiempo real de cuotas, coberturas y ejecución</p>", unsafe_allow_html=True)
    st.write("---")
        
    id_usuario_actual = st.session_state.get("id_usuario_actual", None)
    rol_actual = str(st.session_state.get("rol_actual", "")).lower().strip()
    
    # Declarar variable globalmente para evitar UnboundLocalError
    bloquear_edicion = False
    supervisor_seleccionado = id_usuario_actual

    # Mapeo de filtros en la pantalla principal
    if rol_actual in ["admin", "1", "coordinador", "2"]:
        # Obtener lista de supervisores
        if rol_actual in ["coordinador", "2"]:
            # Obtener región del usuario actual
            try:
                user_prof = UserProfile.objects.get(id_usuario=id_usuario_actual)
                id_region_usuario = user_prof.id_region
            except Exception:
                id_region_usuario = 0
            sups = UserProfile.objects.filter(id_rol=3, id_region=id_region_usuario)
        else:
            sups = UserProfile.objects.filter(id_rol=3) # 3 es supervisor
            
        if not sups.exists():
            sups = UserProfile.objects.all()
            
        lista_sups = [f"{s.id_usuario} - {s.nombre}" for s in sups]
        
        col_sup, col_asesor = st.columns(2)
        with col_sup:
            opciones_sups = ["Todos"] + [f"{s.id_usuario} - {s.nombre}" for s in sups]
            sup_box = st.selectbox("Filtrar por Supervisor:", opciones_sups)
            if sup_box != "Todos":
                id_sup_filtro = int(sup_box.split(" - ")[0].strip())
                supervisor_seleccionado = id_sup_filtro
            else:
                supervisor_seleccionado = "Todos"

        bloquear_edicion = True
    else:
        if not id_usuario_actual:
            st.error("No se encontró sesión de usuario activa.")
            return
        supervisor_seleccionado = id_usuario_actual
        col_asesor = st.container()

    # Obtener los asesores del supervisor seleccionado o de todos los permitidos
    if supervisor_seleccionado == "Todos":
        if rol_actual in ["coordinador", "2"]:
            ids_sups = sups.values_list('id_usuario', flat=True)
            asesores_qs = Asesor.objects.filter(id_usuario__in=ids_sups)
        else:
            asesores_qs = Asesor.objects.all()
    else:
        asesores_qs = Asesor.objects.filter(id_usuario=supervisor_seleccionado)
    
    if not asesores_qs.exists():
        st.info("No se encontraron asesores vinculados para el supervisor seleccionado.")
        return

    lista_asesores = [f"{a.id_asesor} - {a.nombre_asesor}" for a in asesores_qs]
    
    with col_asesor:
        asesor_sel = st.selectbox("Seleccione el Asesor Comercial:", lista_asesores)
    
    id_asesor_fn = asesor_sel.split(" - ")[0].strip()
    asesor_obj = Asesor.objects.get(id_asesor=id_asesor_fn)
    
    try:
        clientes_maestra = float(asesor_obj.maestra) if asesor_obj.maestra else 125.0
    except:
        clientes_maestra = 125.0

    try:
        maestra_rebanadoras = float(asesor_obj.maestra_rebanadoras) if asesor_obj.maestra_rebanadoras else 40.0
    except:
        maestra_rebanadoras = 40.0

    st.info(f"📋 **Ruta:** {id_asesor_fn} | **Asesor:** {asesor_obj.nombre_asesor} | **Universo Maestra:** {int(clientes_maestra)} clientes")

    categorias = list(Categoria.objects.all())
    if not categorias:
        st.warning("No hay categorías configuradas en la base de datos.")
        return

    tab_activacion, tab_volumen, tab_profundidad = st.tabs([
        "🎯 Activación", "📦 Volumen", "🧬 Profundidad de Línea"
    ])

    with tab_activacion:
        st.markdown("##### Evaluación de Activación de Clientes")
        data_act = []
        for cat in categorias:
            seg = SeguimientoDiario.objects.filter(id_asesor=id_asesor_fn, id_categoria=cat.id_categoria).first()
            lleva = float(seg.act_lleva) if seg else 0.0

            nombre_cat = cat.nombre_categoria.lower()
            if "cocidos" in nombre_cat or "reban" in nombre_cat or "jamon" in nombre_cat or "jamón" in nombre_cat:
                universo_actual = maestra_rebanadoras
                tag_universo = f"{int(maestra_rebanadoras)} (Rebanadoras)"
            else:
                universo_actual = clientes_maestra
                tag_universo = f"{int(clientes_maestra)} (General)"

            is_percentage = str(cat.tipo_obj_activacion).lower().strip() == "porcentaje"
            meta_val = float(cat.obj_activacion) if cat.obj_activacion else 0.0

            if is_percentage:
                meta_config = f"{int(meta_val)}%"
                req = (meta_val / 100.0) * universo_actual
            else:
                meta_config = f"{int(meta_val)}"
                req = meta_val

            if req > universo_actual:
                req = universo_actual

            req = int(req + 0.5)
            porc = (lleva / req * 100) if req > 0 else 0.0

            data_act.append({
                "ID_Categoria": cat.id_categoria,
                "Categoria": cat.nombre_categoria,
                "Maestra": tag_universo,
                "Meta Categoria": meta_config,
                "Meta Asesor": req,
                "Avance": lleva,
                "Activación del Día": 0.0,
                "% Cumplimiento": f"{round(porc, 1)}%"
            })
        
        df_act = pd.DataFrame(data_act)
        if df_act.empty:
            df_act = pd.DataFrame(columns=["Categoria", "Maestra", "Meta Categoria", "Meta Asesor", "Avance", "Activación del Día", "% Cumplimiento"] + ["ID_Categoria"])
        
        cols_act = ["Categoria", "Maestra", "Meta Categoria", "Meta Asesor", "Avance", "Activación del Día", "% Cumplimiento"]
        if bloquear_edicion:
            cols_act.remove("Activación del Día")
        
        editor_act = st.data_editor(
            df_act[cols_act + ["ID_Categoria"]],
            hide_index=True,
            use_container_width=True,
            disabled=["Categoria", "Maestra", "Meta Categoria", "Meta Asesor", "Avance", "% Cumplimiento"] if not bloquear_edicion else cols_act,
            column_order=cols_act,
            key=f"edit_act_{id_asesor_fn}"
        )

    with tab_volumen:
        st.markdown("##### Evaluación de Volumen de Ventas")
        data_vol = []
        for cat in categorias:
            rel = AsesorCategoria.objects.filter(id_asesor=id_asesor_fn, id_categoria=cat.id_categoria).first()
            meta_config = float(rel.obj_volumen) if rel else 0.0
            
            seg = SeguimientoDiario.objects.filter(id_asesor=id_asesor_fn, id_categoria=cat.id_categoria).first()
            lleva = float(seg.vol_lleva) if seg else 0.0
            
            if meta_config > 0.0:
                # Si la categoría no tiene meta de volumen asignada, usar 100% por defecto
                pct_vol = float(cat.obj_volumen) if cat.obj_volumen else 100.0
                # Calcular la meta para el asesor y redondear al entero más cercano (arriba si >0.5)
                debe_meta = meta_config * (pct_vol / 100.0)
                debe_meta_val = int(debe_meta + 0.5)
                porc = (lleva / debe_meta_val * 100) if debe_meta_val > 0 else 0.0
                meta_pct_str = f"{int(pct_vol)}%"
                cumplimiento_str = f"{round(porc, 1)}%"
            else:
                meta_pct_str = ""
                debe_meta_val = ""
                cumplimiento_str = ""

            data_vol.append({
                "ID_Categoria": cat.id_categoria,
                "Categoria": cat.nombre_categoria,
                "Tipo Medida": cat.tipo_medida,
                "Obj Volumen": meta_config,
                "Meta Categoria": meta_pct_str,
                "Meta Asesor": debe_meta_val,
                "Avance": lleva,
                "Venta del Día": 0.0,
                "% Cumplimiento": cumplimiento_str
            })
        
        df_vol = pd.DataFrame(data_vol)
        if df_vol.empty:
            df_vol = pd.DataFrame(columns=["Categoria", "Tipo Medida", "Obj Volumen", "Meta Categoria", "Meta Asesor", "Avance", "Venta del Día", "% Cumplimiento"] + ["ID_Categoria"])
        
        cols_vol = ["Categoria", "Tipo Medida", "Obj Volumen", "Meta Categoria", "Meta Asesor", "Avance", "Venta del Día", "% Cumplimiento"]
        if bloquear_edicion:
            cols_vol.remove("Venta del Día")
        
        editor_vol = st.data_editor(
            df_vol[cols_vol + ["ID_Categoria"]],
            hide_index=True,
            use_container_width=True,
            disabled=["Categoria", "Tipo Medida", "Obj Volumen", "Meta Categoria", "Meta Asesor", "Avance", "% Cumplimiento"] if not bloquear_edicion else cols_vol,
            column_order=cols_vol,
            key=f"edit_vol_{id_asesor_fn}"
        )

    with tab_profundidad:
        st.markdown("##### Evaluación de Profundidad de Línea")
        # Obtener la maestra y maestra de rebanadora del asesor una sola vez
        asesor_obj = Asesor.objects.filter(id_asesor=id_asesor_fn).first()
        maestra_val = getattr(asesor_obj, "maestra", "") if asesor_obj else ""
        maestra_rebanadora_val = getattr(asesor_obj, "maestra_rebanadoras", "") if asesor_obj else ""
        data_prof = []
        for cat in categorias:
            seg = SeguimientoDiario.objects.filter(id_asesor=id_asesor_fn, id_categoria=cat.id_categoria).first()
            lleva_prof = float(seg.prof_lleva) if seg else 0.0
            meta_prof = float(cat.obj_profundidad) if cat.obj_profundidad else 0.0
            # Meta SKU should display the depth objective (obj_profundidad)
            meta_sku = float(cat.obj_profundidad) if cat.obj_profundidad else 0.0
            # Seleccionar maestra adecuada: jamón usa maestra_rebanadora
            if "jamon" in cat.nombre_categoria.lower():
                maestra_usada = maestra_rebanadora_val
            else:
                maestra_usada = maestra_val
            porc_prof = (lleva_prof / meta_prof * 100) if meta_prof > 0 else 0.0
            data_prof.append({
                "ID_Categoria": cat.id_categoria,
                "Categoria": cat.nombre_categoria,
                "Maestra": maestra_usada,
                "Total de SKUs activos por cliente": int(meta_sku),
                "Avance": lleva_prof,
                "Carga Diaria": 0.0,
                "% Cumplimiento": f"{round(porc_prof, 1)}%",
            })
        df_prof = pd.DataFrame(data_prof)
        cols_prof = ["Categoria", "Maestra", "Total de SKUs activos por cliente", "Avance", "Carga Diaria", "% Cumplimiento"]
        if bloquear_edicion:
            cols_prof.remove("Carga Diaria")
        editor_prof = st.data_editor(
            df_prof[cols_prof + ["ID_Categoria"]],
            hide_index=True,
            use_container_width=True,
            disabled=["Categoria", "Maestra", "Total de SKUs activos por cliente", "Avance"] if not bloquear_edicion else cols_prof,
            column_order=cols_prof,
            key=f"edit_prof_{id_asesor_fn}"
        )

    if not bloquear_edicion:
        st.write("---")
        if st.button(f"💾 Guardar Reporte Diario de la Ruta {id_asesor_fn}", type="primary", use_container_width=True):
            with st.spinner("Guardando métricas de control diario en la Base de Datos..."):
                try:
                    for cat in categorias:
                        cid = cat.id_categoria
                        
                        # Obtener los valores acumulados actuales en la base de datos
                        seg_db = SeguimientoDiario.objects.filter(id_asesor=id_asesor_fn, id_categoria=cid).first()
                        orig_act = float(seg_db.act_lleva) if seg_db else 0.0
                        orig_vol = float(seg_db.vol_lleva) if seg_db else 0.0
                        orig_prof = float(seg_db.prof_lleva) if seg_db else 0.0

                        # Obtener los valores diarios ingresados por el usuario
                        row_act = editor_act[editor_act["ID_Categoria"] == cid]
                        daily_act = float(row_act.iloc[0]["Activación del Día"]) if not row_act.empty else 0.0

                        row_vol = editor_vol[editor_vol["ID_Categoria"] == cid]
                        daily_vol = float(row_vol.iloc[0]["Venta del Día"]) if not row_vol.empty else 0.0

                        row_prof = editor_prof[editor_prof["ID_Categoria"] == cid]
                        daily_prof = float(row_prof.iloc[0]["Carga Diaria"]) if not row_prof.empty else 0.0
                        
                        # Sumar el diario al acumulado
                        val_act = orig_act + daily_act
                        val_vol = orig_vol + daily_vol
                        val_prof = orig_prof + daily_prof
                        
                        SeguimientoDiario.objects.update_or_create(
                            id_asesor=id_asesor_fn,
                            id_categoria=cid,
                            defaults={
                                "act_lleva": val_act,
                                "vol_lleva": val_vol,
                                "prof_lleva": val_prof
                            }
                        )

                        # Guardar registro diario en el historial si tiene movimientos
                        if daily_act > 0 or daily_vol > 0 or daily_prof > 0:
                            from comercial.models import RegistroDiario
                            from django.utils import timezone
                            RegistroDiario.objects.create(
                                fecha=timezone.localdate(),
                                id_asesor=id_asesor_fn,
                                id_categoria=cid,
                                act_dia=daily_act,
                                vol_dia=daily_vol,
                                prof_dia=daily_prof
                            )
                    
                    st.success(f"🎯 ¡Seguimiento diario de la ruta {id_asesor_fn} guardado y sumado con éxito!")
                    import time
                    time.sleep(2)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error crítico al guardar seguimiento: {e}")
    else:
        st.info("ℹ️ Estás visualizando este reporte en modo de consulta (Lectura). Los cambios en la cuadrícula no se guardarán.")