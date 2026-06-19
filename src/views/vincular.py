# src/views/vincular.py
import streamlit as st

def show_vincular():
    # =========================================================
    # ⚡ ENCAPSULAMIENTO DE LIBRERÍAS PESADAS (Optimización Global)
    # =========================================================
    import pandas as pd
    from comercial.models import Asesor, Categoria, AsesorCategoria

    # Título estático inicial rápido
    st.title("👤 Gestión Integral de Asesores Comerciales")
    st.markdown("<p style='color: #A0AAB2;'>Monitoreo en tiempo real de cuotas, coberturas y ejecución</p>", unsafe_allow_html=True)
    st.write("---")
    
    rol_limpio = str(st.session_state.get("rol_actual", "")).lower().strip()
    id_usuario_actual = st.session_state.get("id_usuario_actual", None)

    if rol_limpio not in ["supervisor", "3", "admin", "1"]:
        st.warning("⚠️ Este módulo es exclusivo para perfiles de Supervisor.")
        return

    pestana_asesores, pestana_registrar_nuevo, pestana_editar_maestras, pestana_editar_volumen = st.tabs([
        "📝 Lista de Asesores", 
        "➕ Registrar Nuevo Asesor",
        "⚙️ Editar Carteras Maestras",
        "📊 Editar Objetivos de Volumen"
    ])

    # =========================================================================
    # PESTAÑA 1: LISTA DE ASESORES
    # =========================================================================
    with pestana_asesores:
            st.markdown("#### 👥 Asesores en tu equipo actualmente")
            asesores_equipo = Asesor.objects.filter(id_usuario=id_usuario_actual)
            if asesores_equipo.exists():
                df_equipo = pd.DataFrame.from_records(asesores_equipo.values('id_asesor', 'nombre_asesor', 'maestra', 'maestra_rebanadoras'))
                df_equipo = df_equipo.rename(columns={
                    'id_asesor': 'ID Ruta', 'nombre_asesor': 'Nombre del Asesor',
                    'maestra': 'Cartera Maestra', 'maestra_rebanadoras': 'Maestra Rebanadoras'
                })
                st.dataframe(df_equipo, use_container_width=True, hide_index=True)
            else:
                st.info("Aún no tienes asesores vinculados a tu perfil.")

    # =========================================================================
    # PESTAÑA 2: REGISTRAR NUEVO ASESOR
    # =========================================================================
    with pestana_registrar_nuevo:
        st.subheader("Registrar Nuevo Asesor")
        
        with st.form("form_registrar_nuevo"):
            col1, col2 = st.columns(2)
            with col1:
                id_asesor_nuevo = st.text_input("Código de Ruta (ID Asesor)")
            with col2:
                nombre_asesor = st.text_input("Nombre Completo")
                
            col3, col4 = st.columns(2)
            with col3:
                maestra_input = st.number_input("Cartera Maestra (Total Clientes)", min_value=0, step=1)
            with col4:
                maestra_reb_input = st.number_input("Cartera Maestra Rebanadoras", min_value=0, step=1)
                
            st.write("---")
            btn_registrar = st.form_submit_button("💾 Registrar Asesor", type="primary", use_container_width=True)
            
            if btn_registrar:
                id_asesor_nuevo = id_asesor_nuevo.strip().upper()
                if not id_asesor_nuevo or not nombre_asesor.strip():
                    st.error("⚠️ El Código de Ruta y el Nombre son obligatorios.")
                elif Asesor.objects.filter(id_asesor=id_asesor_nuevo).exists():
                    st.error(f"❌ El código de ruta **{id_asesor_nuevo}** ya existe en el sistema.")
                else:
                    try:
                        Asesor.objects.create(
                            id_asesor=id_asesor_nuevo,
                            nombre_asesor=nombre_asesor.strip(),
                            id_usuario=id_usuario_actual,
                            maestra=str(maestra_input),
                            maestra_rebanadoras=str(maestra_reb_input)
                        )
                        st.success(f"¡Asesor {nombre_asesor} registrado y asignado a tu equipo!")
                        import time
                        time.sleep(2)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar en base de datos: {e}")

    # =========================================================================
    # PESTAÑA 3: EDITAR CARTERAS MAESTRAS
    # =========================================================================
    with pestana_editar_maestras:
        st.subheader("Editar Carteras Maestras de sus Asesores")
        if asesores_equipo.exists():
            lista_asesores_equipo = [f"{a.id_asesor} - {a.nombre_asesor}" for a in asesores_equipo]
            asesor_sel = st.selectbox("Seleccione un Asesor de su equipo", [""] + lista_asesores_equipo)
            
            if asesor_sel:
                try:
                    a_id = asesor_sel.split(" - ")[0]
                    a_obj = Asesor.objects.get(id_asesor=a_id)
                    valor_maestra = int(a_obj.maestra) if a_obj.maestra and str(a_obj.maestra).isdigit() else 0
                    valor_maestra_reb = int(a_obj.maestra_rebanadoras) if a_obj.maestra_rebanadoras and str(a_obj.maestra_rebanadoras).isdigit() else 0
                except Exception:
                    valor_maestra = 0
                    valor_maestra_reb = 0
                
                with st.form("form_carteras_maestras"):
                    col1, col2 = st.columns(2)
                    with col1:
                        m_input = st.number_input("Cartera Maestra (Total Clientes)", min_value=0, step=1, value=valor_maestra)
                    with col2:
                        r_input = st.number_input("Cartera Maestra Rebanadoras", min_value=0, step=1, value=valor_maestra_reb)
                    
                    if st.form_submit_button("Guardar Carteras", type="primary", use_container_width=True):
                        try:
                            a_obj.maestra = str(m_input)
                            a_obj.maestra_rebanadoras = str(r_input)
                            a_obj.save()
                            st.success("¡Carteras actualizadas correctamente!")
                            import time
                            time.sleep(2)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
            else:
                st.info("💡 Por favor seleccione un asesor de la lista superior para editar sus carteras.")
        else:
            st.warning("⚠️ Primero debes vincular asesores a tu equipo.")

    # =========================================================================
    # PESTAÑA 4: OBJETIVOS DE VOLUMEN
    # =========================================================================
    with pestana_editar_volumen:
        st.subheader("Configurar Objetivos de Volumen por Categoría")
        if asesores_equipo.exists():
            lista_asesores_equipo = [f"{a.id_asesor} - {a.nombre_asesor}" for a in asesores_equipo]
            col_sel1, col_sel2 = st.columns(2)
            with col_sel1:
                asesor_sel_cat = st.selectbox("Seleccione el Asesor para configurar volumen", [""] + lista_asesores_equipo)
            with col_sel2:
                mes_sel_cat = st.selectbox("Seleccione el Mes para configurar volumen", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
            
            if asesor_sel_cat and mes_sel_cat:
                id_asesor_cat = asesor_sel_cat.split(" - ")[0]
                categorias = Categoria.objects.filter(mes=mes_sel_cat)
                
                if not categorias.exists():
                    st.info(f"⚠️ No hay categorías foco registradas para el mes de {mes_sel_cat}.")
                else:
                    with st.form("form_volumen"):
                        volumen_data = {}
                        for cat in categorias:
                            obj_actual = AsesorCategoria.objects.filter(id_asesor=id_asesor_cat, id_categoria=cat.id_categoria).first()
                            valor_inicial = float(obj_actual.obj_volumen) if obj_actual else 0.0
                            volumen_data[cat.id_categoria] = st.number_input(f"Objetivo Volumen - {cat.nombre_categoria}", value=valor_inicial, min_value=0.0, step=1.0)
                        
                        if st.form_submit_button("Guardar Objetivos de Volumen", type="primary", use_container_width=True):
                            try:
                                for id_cat, valor in volumen_data.items():
                                    if valor == 0.0:
                                        AsesorCategoria.objects.filter(id_asesor=id_asesor_cat, id_categoria=id_cat).delete()
                                    else:
                                        AsesorCategoria.objects.update_or_create(id_asesor=id_asesor_cat, id_categoria=id_cat, defaults={'obj_volumen': valor})
                                st.success("¡Objetivos actualizados exitosamente!")
                                import time
                                time.sleep(2)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
        else:
            st.warning("⚠️ Primero debes vincular asesores a tu equipo.")