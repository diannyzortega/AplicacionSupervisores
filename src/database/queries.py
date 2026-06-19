# src/database/queries.py
import streamlit as st
import pandas as pd
from comercial.models import PlanificacionSemanal, ResultadosTarde, Region, Rol, Sucursal, UserProfile, Asesor, Categoria, AsesorCategoria, RegistroDiario

MODEL_MAPPING = {
    "Planificacion_Semanal": PlanificacionSemanal,
    "Resultados_Tarde": ResultadosTarde,
    "T_Regiones": Region,
    "T_Rol": Rol,
    "T_Sucursales": Sucursal,
    "T_Usuarios": UserProfile,
    "T_Asesores": Asesor,
    "T_Categorias": Categoria,
    "T_Asesor_Categorias": AsesorCategoria,
    "T_Registro_Diario": RegistroDiario
}

COLUMN_MAPPING = {
    "Planificacion_Semanal": {
        'fecha': 'Fecha', 'supervisor': 'Supervisor', 'region': 'Región', 'sucursal': 'Sucursal', 
        'modalidad': 'Modalidad', 'acompanamiento': 'Acompañamiento', 'asesor': 'Asesor', 'zona': 'Zona', 
        'clientes_actuales': 'Clientes_Actuales', 'clientes_captar': 'Clientes_Captar', 
        'objetivo_principal': 'Objetivo_Principal', 'enfoque': 'Enfoque', 
        'auditoria_jamones': 'Auditoria_Jamones', 'auditoria_quesos': 'Auditoria_Quesos', 
        'monto_proyectado_cobro': 'Monto_Proyectado_Cobro', 'cajas_objetivo': 'Cajas_Objetivo', 
        'kilos_objetivo': 'Kilos_Objetivo'
    },
    "Resultados_Tarde": {
        'fecha_cierre': 'Fecha_Cierre', 'supervisor': 'Supervisor', 'region': 'Región', 'sucursal': 'Sucursal', 
        'total_clientes_dia': 'Total_Clientes_Dia', 'clts_a_captar': 'Clts_a_Captar', 
        'meta_cajas_matutina': 'Meta_Cajas_Matutina', 'meta_kilos_matutina': 'Meta_Kilos_Matutina', 
        'meta_cobranza_matutina': 'Meta_Cobranza_Matutina', 'cajas_reales': 'Cajas_Reales', 
        'kilos_reales': 'Kilos_Reales', 'monto_cobrado_real': 'Monto_Cobrado_Real', 
        'clientes_activados': 'Clientes_Activados', 'clientes_apertura_nuevos': 'Clientes_Apertura_Nuevos', 
        'clts_visita_con_pop': 'Clts_Visita_Con_POP', 'clts_con_1_sku': 'Clts_Con_1_SKU', 
        'clts_con_2_sku': 'Clts_Con_2_SKU', 'clts_con_mas_3_sku': 'Clts_Con_Mas_3_SKU', 
        'cumplio_pasos_visita': 'Cumplio_Pasos_Visita', 'usa_catalogo': 'Usa_Catalogo', 
        'calidad_atencion': 'Calidad_Atencion', 'audito_jamon': 'Audito_Jamon', 
        'obs_jamon_concurso': 'Obs_Jamon_Concurso', 'audito_queso': 'Audito_Queso', 
        'obs_queso_concurso': 'Obs_Queso_Concurso', 'cumplimiento_plan': 'Cumplimiento_Plan', 
        'novedades_market': 'Novedades_Market'
    },
    "T_Regiones": {'id_region': 'ID_Region', 'nombre_region': 'Nombre_Region'},
    "T_Rol": {'id_rol': 'ID_Rol', 'nombre_rol': 'Nombre_Rol'},
    "T_Sucursales": {'id_sucursal': 'ID_Sucursal', 'nombre_sucursal': 'Nombre_Sucursal', 'id_region': 'ID_Region'},
    "T_Usuarios": {'id_usuario': 'ID_Usuario', 'nombre': 'Nombre', 'id_rol': 'ID_Rol', 'id_region': 'ID_Region', 'id_sucursal': 'ID_Sucursal'},
    "T_Asesores": {'id_asesor': 'ID_Asesor', 'nombre_asesor': 'Nombre_Asesor', 'id_usuario': 'ID_Usuario', 'maestra': 'Maestra', 'maestra_rebanadoras': 'Maestra_Rebanadoras'},
    "T_Categorias": {'id_categoria': 'ID_Categoria', 'nombre_categoria': 'Nombre_Categoria', 'id_region': 'ID_Region', 'obj_activacion': 'Obj_Activacion', 'tipo_obj_activacion': 'Tipo_Obj_Activacion', 'obj_volumen': 'Obj_Volumen', 'obj_profundidad': 'Obj_Profundidad', 'mes': 'Mes'},
    "T_Asesor_Categorias": {'id_asesor': 'ID_Asesor', 'id_categoria': 'ID_Categoria', 'obj_volumen': 'Obj_Volumen'},
    "T_Registro_Diario": {'fecha': 'Fecha', 'id_asesor': 'ID_Asesor', 'id_categoria': 'ID_Categoria', 'act_dia': 'Act_Dia', 'vol_dia': 'Vol_Dia', 'prof_dia': 'Prof_Dia'}
}

@st.cache_data(ttl=600)
def cargar_tabla_cached(sheet_name):
    if sheet_name in MODEL_MAPPING:
        model = MODEL_MAPPING[sheet_name]
        if sheet_name == "T_Usuarios":
            qs = model.objects.select_related('user').all()
            data = []
            for profile in qs:
                data.append({
                    'ID_Usuario': profile.id_usuario,
                    'Nombre': profile.nombre,
                    'ID_Rol': profile.id_rol,
                    'ID_Region': profile.id_region,
                    'ID_Sucursal': profile.id_sucursal,
                    'User': profile.user.username if profile.user else "",
                    'Clave': '********' if profile.user else ""
                })
            df = pd.DataFrame(data)
            if df.empty:
                df = pd.DataFrame(columns=['ID_Usuario', 'Nombre', 'ID_Rol', 'ID_Region', 'ID_Sucursal', 'User', 'Clave'])
            return df

        qs = model.objects.all().values()
        df = pd.DataFrame.from_records(qs)
        if not df.empty and sheet_name in COLUMN_MAPPING:
            df = df.rename(columns=COLUMN_MAPPING[sheet_name])
            if 'id' in df.columns:
                df = df.drop(columns=['id'])
            if 'user_id' in df.columns:
                df = df.drop(columns=['user_id'])
        elif df.empty:
            cols = list(COLUMN_MAPPING.get(sheet_name, {}).values())
            df = pd.DataFrame(columns=cols)
        return df
    return pd.DataFrame()

def actualizar_tabla_excel(df, sheet_name, rerun=True):
    try:
        if sheet_name in MODEL_MAPPING:
            model = MODEL_MAPPING[sheet_name]
            df_limpio = df.fillna("")
            
            if sheet_name == "T_Usuarios":
                from django.contrib.auth.models import User
                existing_user_ids = []
                
                for index, row in df_limpio.iterrows():
                    id_usuario = int(row['ID_Usuario'])
                    nombre = str(row['Nombre'])
                    username = str(row['User'])
                    password = str(row['Clave'])
                    id_rol = int(row['ID_Rol'])
                    id_region = int(row['ID_Region'])
                    id_sucursal = int(row['ID_Sucursal'])
                    
                    existing_user_ids.append(id_usuario)
                    
                    try:
                        profile = model.objects.get(id_usuario=id_usuario)
                        profile.nombre = nombre
                        profile.id_rol = id_rol
                        profile.id_region = id_region
                        profile.id_sucursal = id_sucursal
                        profile.save()
                        
                        user = profile.user
                        if user.username != username:
                            user.username = username
                            user.save()
                        if password != '********' and password.strip() != '':
                            user.set_password(password)
                            user.save()
                    except model.DoesNotExist:
                        user = User.objects.create_user(username=username, password=password)
                        model.objects.create(
                            user=user,
                            id_usuario=id_usuario,
                            nombre=nombre,
                            id_rol=id_rol,
                            id_region=id_region,
                            id_sucursal=id_sucursal
                        )
                
                profiles_to_delete = model.objects.exclude(id_usuario__in=existing_user_ids)
                for p in profiles_to_delete:
                    user = p.user
                    p.delete()
                    if user:
                        user.delete()
                
                st.cache_data.clear()
                return

            # Reverse column mapping (Lleva los nombres de la interfaz a los nombres del Modelo Django)
            mapping_actual = COLUMN_MAPPING.get(sheet_name, {})
            reverse_mapping = {v: k for k, v in mapping_actual.items()}
            df_db = df_limpio.rename(columns=reverse_mapping)
            
            # Convertimos a registros para Django
            records = df_db.to_dict(orient="records")
            st.write(f"🛠️ Procesados {len(records)} registros para la hoja {sheet_name}")
            
            pk_field = model._meta.pk.name
            for rec in records:
                pk_val = rec.get(pk_field)
                if pk_val is not None and str(pk_val).strip() != "":
                    # Limpiamos el dict de defaults
                    defaults_dict = rec.copy()
                    defaults_dict.pop(pk_field, None)
                    defaults_dict.pop('id', None) # Quitar id implícito si existe para evitar conflictos
                    
                    # Convertir pk_val al tipo adecuado si es numérico
                    if pk_field in ['id_categoria', 'id_region', 'id_sucursal']:
                        try:
                            pk_val = int(pk_val)
                        except:
                            pass
                            
                    model.objects.update_or_create(**{pk_field: pk_val}, defaults=defaults_dict)
                else:
                    # Búsqueda tolerante: intenta minúscula (Django) o Mayúscula (Vista)
                    supervisor_val = rec.get('supervisor') or rec.get('Supervisor')
                    
                    if model.__name__ == 'ResultadosTarde':
                        date_field_name = 'fecha_cierre'
                        date_val = rec.get('fecha_cierre') or rec.get('Fecha_Cierre') or rec.get('Fecha')
                    else:
                        date_field_name = 'fecha'
                        date_val = rec.get('fecha') or rec.get('Fecha')
                    
                    # Normalizamos las llaves críticas en el diccionario para Django
                    if supervisor_val and date_val:
                        rec[date_field_name] = date_val
                        rec['supervisor'] = supervisor_val
                        
                        # Quitamos duplicados visuales si existen para evitar conflictos con Django
                        rec.pop('Supervisor', None)
                        rec.pop('Fecha', None)
                        rec.pop('Fecha_Cierre', None)
                        
                        lookup_kwargs = {date_field_name: date_val, 'supervisor': supervisor_val}
                        model.objects.update_or_create(defaults=rec, **lookup_kwargs)
                    else:
                        # Fallback de seguridad si no se hallan campos clave estructurados
                        model.objects.create(**rec)

            st.cache_data.clear()
            if rerun:
                st.rerun()
                
    except Exception as e:
        # Aquí cerramos correctamente el bloque que se quedaba colgado
        st.error(f"Error crítico al actualizar la base de datos Django: {e}")
        st.error(f"Error al actualizar la base de datos Django: {e}")