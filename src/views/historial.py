# src/views/historial.py
import streamlit as st
import pandas as pd
from comercial.models import RegistroDiario, Asesor, Categoria

def show_historial():
    st.title("📅 Historial de Cargas Diarias")
    st.markdown("<p style='color: #A0AAB2;'>Consulte el histórico de ventas, activaciones y mix de productos ingresados diariamente</p>", unsafe_allow_html=True)
    st.write("---")

    # 1. Mapeo de rol, región y supervisores
    from comercial.models import UserProfile
    rol_actual = str(st.session_state.get("rol_actual", "")).lower().strip()
    id_usuario_actual = st.session_state.get("id_usuario_actual", None)

    try:
        user_prof = UserProfile.objects.get(id_usuario=id_usuario_actual)
        id_region_usuario = user_prof.id_region
    except Exception:
        id_region_usuario = 0

    # Determinar supervisores permitidos y asesores base
    if rol_actual in ["admin", "1"]:
        sups_qs = UserProfile.objects.filter(id_rol=3)
        asesores_qs = Asesor.objects.all()
    elif rol_actual in ["coordinador", "2"]:
        sups_qs = UserProfile.objects.filter(id_rol=3, id_region=id_region_usuario)
        ids_sups = sups_qs.values_list('id_usuario', flat=True)
        asesores_qs = Asesor.objects.filter(id_usuario__in=ids_sups)
    else:  # Supervisor
        sups_qs = UserProfile.objects.none()
        asesores_qs = Asesor.objects.filter(id_usuario=id_usuario_actual)

    # Renderizar filtros en columnas
    # Si es Admin o Coordinador, mostramos filtro de supervisor arriba
    if rol_actual in ["admin", "1", "coordinador", "2"]:
        col_sup, col_agrupar_sub, col_periodo_sel = st.columns(3)
        with col_sup:
            opciones_sups = ["Todos"] + [f"{s.id_usuario} - {s.nombre}" for s in sups_qs]
            sup_sel = st.selectbox("Filtrar por Supervisor:", opciones_sups)
            
            if sup_sel != "Todos":
                id_sup_filtro = int(sup_sel.split(" - ")[0].strip())
                asesores_qs = asesores_qs.filter(id_usuario=id_sup_filtro)
        with col_agrupar_sub:
            opcion_agrupar = st.selectbox("Ver acumulado por:", ["Día", "Semana", "Mes"])
    else:
        col_agrupar, col_periodo_sel = st.columns(2)
        with col_agrupar:
            opcion_agrupar = st.selectbox("Ver acumulado por:", ["Día", "Semana", "Mes"])
            
    placeholder_periodo = col_periodo_sel.empty()

    # Selector de Asesor y Categoría
    col_asesor, col_cat = st.columns(2)
    
    asesores_dict = {a.id_asesor: a.nombre_asesor for a in asesores_qs}
    categorias_dict = {c.id_categoria: c.nombre_categoria for c in Categoria.objects.all()}

    with col_asesor:
        opciones_asesor = ["Todos"] + [f"{k} - {v}" for k, v in asesores_dict.items()]
        asesor_sel = st.selectbox("Filtrar por Asesor:", opciones_asesor)

    with col_cat:
        opciones_cat = ["Todas"] + [f"{k} - {v}" for k, v in categorias_dict.items()]
        categoria_sel = st.selectbox("Filtrar por Categoría:", opciones_cat)

    # Query inicial filtrado a los asesores permitidos
    ids_asesores_permitidos = list(asesores_qs.values_list('id_asesor', flat=True))
    qs = RegistroDiario.objects.filter(id_asesor__in=ids_asesores_permitidos)

    # Aplicar filtros de base de datos
    if asesor_sel != "Todos":
        id_asesor_filtro = asesor_sel.split(" - ")[0]
        qs = qs.filter(id_asesor=id_asesor_filtro)

    if categoria_sel != "Todas":
        id_cat_filtro = int(categoria_sel.split(" - ")[0])
        qs = qs.filter(id_categoria=id_cat_filtro)

    if not qs.exists():
        st.info("No se encontraron registros cargados que coincidan con los filtros seleccionados.")
        return

    # Convertir a DataFrame
    df = pd.DataFrame(list(qs.values('fecha', 'id_asesor', 'id_categoria', 'act_dia', 'vol_dia', 'prof_dia')))
    df['fecha'] = pd.to_datetime(df['fecha'])

    # Mapear nombres de Asesor y Categoría
    df['Asesor'] = df['id_asesor'].map(asesores_dict).fillna(df['id_asesor'])
    df['Categoría'] = df['id_categoria'].map(categorias_dict).fillna(df['id_categoria'].astype(str))

    # Definir columna de Periodo según la agrupación seleccionada
    if opcion_agrupar == "Día":
        df['Periodo'] = df['fecha'].dt.strftime('%Y-%m-%d')
    elif opcion_agrupar == "Semana":
        df['Periodo'] = df['fecha'].dt.strftime('%Y-W%V')
    else:  # Mes
        meses_es = {
            1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
            7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
        }
        df['Periodo'] = df['fecha'].apply(lambda x: f"{x.year} - {meses_es[x.month]}")

    # Obtener valores de períodos únicos disponibles
    periodos_disponibles = sorted(df['Periodo'].unique(), reverse=True)
    
    # Renderizar el selector dinámico
    with placeholder_periodo:
        opcion_periodo = st.selectbox(f"Seleccionar {opcion_agrupar} Específico:", ["Todos"] + periodos_disponibles)

    # Filtrar por período seleccionado si no es "Todos"
    if opcion_periodo != "Todos":
        df = df[df['Periodo'] == opcion_periodo]

    # Agrupación y formateo final
    df_group = df.groupby(['Periodo', 'Asesor', 'Categoría'], as_index=False).agg({
        'act_dia': 'sum',
        'vol_dia': 'sum',
        'prof_dia': 'sum'
    })

    # Renombrar columnas para reporte visual premium
    df_group = df_group.rename(columns={
        'Periodo': 'Período',
        'act_dia': 'Activación Acumulada',
        'vol_dia': 'Volumen Venta Acumulado',
        'prof_dia': 'Profundidad Acumulada (Clientes Mix)'
    })

    st.write("---")
    st.write("### 📝 Detalle del Registro Histórico")
    
    st.dataframe(
        df_group,
        use_container_width=True,
        hide_index=True
    )
