"""
Script para comparar datos entre archivo de carga Pyme y archivos BICE (OMG + Pyme).

Compara RUTs y reporta inconsistencias, separando entre empresas OMG y Pyme.

Archivos:
- 20260105_PAWER Asistencia de Mascotas_FULL_Pawer_asist - Pyme.xlsx (CARGA)
- BICE OMG Convenio_users_12_01_2026.xlsx (BICE OMG)
- BICE PYME_users_12_01_2026.xlsx (BICE PYME)

Empresas OMG:
- DDB CHILE SPA
- INFLUENCE & RESEARCH S.A.
- MEDIA INTERACTIVE S A
- OMD CHILE SPA
- OMNICOM MEDIA GROUP CHILE S.A.
- PHD CHILE S.A.

Todas las demás empresas son Pyme.
"""
import pandas as pd
import os
import sys
from datetime import datetime

# Agregar la carpeta padre al path para poder importar utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.normalizers import combinar_rut_dv
from utils.file_handlers import buscar_archivo_en_data


# Empresas que pertenecen a OMG
EMPRESAS_OMG = [
    'DDB CHILE SPA',
    'INFLUENCE & RESEARCH S.A.',
    'MEDIA INTERACTIVE S A',
    'OMD CHILE SPA',
    'OMNICOM MEDIA GROUP CHILE S.A.',
    'PHD CHILE S.A.'
]


def normalizar_rut_comparacion(rut):
    """
    Normaliza un RUT eliminando puntos, guiones y ceros a la izquierda/derecha.
    """
    if not rut or pd.isna(rut):
        return ''
    
    # Convertir a string y limpiar
    rut_str = str(rut).strip().replace('.', '').replace('-', '').replace(' ', '').upper()
    
    if not rut_str:
        return ''
    
    # Eliminar ceros a la izquierda
    rut_str = rut_str.lstrip('0')
    
    # Si quedó vacío después de eliminar ceros, retornar vacío
    if not rut_str:
        return ''
    
    return rut_str


def es_empresa_omg(nombre_empresa):
    """
    Verifica si una empresa pertenece al grupo OMG.
    """
    if not nombre_empresa or pd.isna(nombre_empresa):
        return False
    
    nombre_upper = str(nombre_empresa).upper().strip()
    
    for empresa in EMPRESAS_OMG:
        if empresa.upper() in nombre_upper:
            return True
    
    return False


def comparar_pyme_bice():
    """
    Compara los RUTs entre el archivo de carga y los archivos BICE (OMG + Pyme).
    """
    # Rutas de archivos
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, 'data', 'Bice Pyme & OMG')
    
    # Buscar archivos dinámicamente
    archivo_carga = None
    archivo_bice_omg = None
    archivo_bice_pyme = None
    
    for filename in os.listdir(data_dir):
        # Ignorar archivos temporales de Excel
        if filename.startswith('~$'):
            continue
            
        if 'PAWER Asistencia de Mascotas' in filename and 'Pyme' in filename:
            archivo_carga = os.path.join(data_dir, filename)
        elif 'BICE OMG Convenio' in filename:
            archivo_bice_omg = os.path.join(data_dir, filename)
        elif 'BICE PYME' in filename and 'OMG' not in filename:
            archivo_bice_pyme = os.path.join(data_dir, filename)
    
    if not archivo_carga or not archivo_bice_omg or not archivo_bice_pyme:
        print("❌ Error: No se encontraron todos los archivos necesarios")
        print(f"   Carga encontrado: {archivo_carga is not None}")
        print(f"   BICE OMG encontrado: {archivo_bice_omg is not None}")
        print(f"   BICE Pyme encontrado: {archivo_bice_pyme is not None}")
        return
    
    print("="*80)
    print("📊 COMPARACIÓN CARGA vs BICE (OMG + PYME)")
    print("="*80)
    print(f"\nArchivo Carga: {os.path.basename(archivo_carga)}")
    print(f"Archivo BICE OMG: {os.path.basename(archivo_bice_omg)}")
    print(f"Archivo BICE Pyme: {os.path.basename(archivo_bice_pyme)}")
    
    # Leer archivos
    print("\n🔄 Leyendo archivos...")
    
    # Leer Carga (Excel)
    df_carga = None
    try:
        df_carga = pd.read_excel(archivo_carga)
        print(f"  ✓ Archivo Carga leído correctamente")
    except Exception as e:
        print(f"  ❌ Error al leer archivo de carga: {e}")
        return
    
    # Leer BICE OMG (Excel)
    df_bice_omg = pd.read_excel(archivo_bice_omg)
    print(f"  ✓ Archivo BICE OMG leído correctamente")
    
    # Leer BICE Pyme (Excel)
    df_bice_pyme = pd.read_excel(archivo_bice_pyme)
    print(f"  ✓ Archivo BICE Pyme leído correctamente")
    
    print(f"\n📈 Registros totales:")
    print(f"  - Carga: {len(df_carga)}")
    print(f"  - BICE OMG (total): {len(df_bice_omg)}")
    print(f"  - BICE Pyme (total): {len(df_bice_pyme)}")
    
    # Filtrar solo registros con Estado = VERDADERO en archivos BICE
    if 'Estado' in df_bice_omg.columns:
        df_bice_omg['Estado'] = df_bice_omg['Estado'].astype(str).str.upper()
        df_bice_omg = df_bice_omg[df_bice_omg['Estado'].isin(['VERDADERO', 'TRUE', 'ACTIVO', '1'])].copy()
        print(f"  - BICE OMG (activos): {len(df_bice_omg)}")
    
    if 'Estado' in df_bice_pyme.columns:
        df_bice_pyme['Estado'] = df_bice_pyme['Estado'].astype(str).str.upper()
        df_bice_pyme = df_bice_pyme[df_bice_pyme['Estado'].isin(['VERDADERO', 'TRUE', 'ACTIVO', '1'])].copy()
        print(f"  - BICE Pyme (activos): {len(df_bice_pyme)}")
    
    # Filtrar solo los activos (Estado = VERDADERO) en archivos BICE
    print(f"\n🔍 Filtrando registros activos (Estado = VERDADERO)...")
    
    if 'Estado' in df_bice_omg.columns:
        antes_omg = len(df_bice_omg)
        df_bice_omg = df_bice_omg[df_bice_omg['Estado'].apply(
            lambda x: str(x).upper() in ['TRUE', 'VERDADERO', 'SI', 'SÍ', 'YES', '1', 'ACTIVO']
        )].copy()
        print(f"  ✓ BICE OMG: {len(df_bice_omg)} activos de {antes_omg} totales ({antes_omg - len(df_bice_omg)} inactivos filtrados)")
    else:
        print(f"  ⚠️  BICE OMG: No se encontró columna 'Estado', usando todos los registros")
    
    if 'Estado' in df_bice_pyme.columns:
        antes_pyme = len(df_bice_pyme)
        df_bice_pyme = df_bice_pyme[df_bice_pyme['Estado'].apply(
            lambda x: str(x).upper() in ['TRUE', 'VERDADERO', 'SI', 'SÍ', 'YES', '1', 'ACTIVO']
        )].copy()
        print(f"  ✓ BICE Pyme: {len(df_bice_pyme)} activos de {antes_pyme} totales ({antes_pyme - len(df_bice_pyme)} inactivos filtrados)")
    else:
        print(f"  ⚠️  BICE Pyme: No se encontró columna 'Estado', usando todos los registros")
    
    # Procesar RUTs en Carga
    print("\n🔧 Procesando RUTs...")
    
    # Combinar RUT_ASEGURADO + DV_ASEGURADO en archivo de carga
    if 'RUT_ASEGURADO' in df_carga.columns and 'DV_ASEGURADO' in df_carga.columns:
        df_carga['RUT_COMPLETO'] = df_carga.apply(
            lambda row: combinar_rut_dv(row['RUT_ASEGURADO'], row['DV_ASEGURADO']), 
            axis=1
        )
    else:
        print("❌ Error: No se encontraron columnas RUT_ASEGURADO y DV_ASEGURADO en archivo de carga")
        return
    
    # Normalizar RUTs
    df_carga['RUT_NORM'] = df_carga['RUT_COMPLETO'].apply(normalizar_rut_comparacion)
    df_bice_omg['RUT_NORM'] = df_bice_omg['RUT'].apply(normalizar_rut_comparacion)
    df_bice_pyme['RUT_NORM'] = df_bice_pyme['RUT'].apply(normalizar_rut_comparacion)
    
    # Eliminar RUTs vacíos
    df_carga = df_carga[df_carga['RUT_NORM'] != ''].copy()
    df_bice_omg = df_bice_omg[df_bice_omg['RUT_NORM'] != ''].copy()
    df_bice_pyme = df_bice_pyme[df_bice_pyme['RUT_NORM'] != ''].copy()
    
    print(f"  ✓ RUTs válidos: Carga={len(df_carga)}, BICE OMG={len(df_bice_omg)}, BICE Pyme={len(df_bice_pyme)}")
    
    # Separar OMG de Pyme en archivo de carga según NOMBRE_CONTRATANTE
    print("\n🏢 Clasificando empresas en archivo de carga...")
    
    df_carga['ES_OMG'] = df_carga['NOMBRE_CONTRATANTE'].apply(es_empresa_omg)
    
    df_carga_omg = df_carga[df_carga['ES_OMG'] == True].copy()
    df_carga_pyme = df_carga[df_carga['ES_OMG'] == False].copy()
    
    print(f"  ✓ Registros OMG en Carga: {len(df_carga_omg)}")
    print(f"  ✓ Registros Pyme en Carga: {len(df_carga_pyme)}")
    
    # Obtener sets de RUTs únicos
    ruts_carga_omg = set(df_carga_omg['RUT_NORM'].unique())
    ruts_carga_pyme = set(df_carga_pyme['RUT_NORM'].unique())
    ruts_bice_omg = set(df_bice_omg['RUT_NORM'].unique())
    ruts_bice_pyme = set(df_bice_pyme['RUT_NORM'].unique())
    
    print(f"\n🔢 RUTs únicos:")
    print(f"  - OMG en Carga: {len(ruts_carga_omg)}")
    print(f"  - Pyme en Carga: {len(ruts_carga_pyme)}")
    print(f"  - BICE OMG: {len(ruts_bice_omg)}")
    print(f"  - BICE Pyme: {len(ruts_bice_pyme)}")
    
    # Realizar comparaciones
    print("\n🔍 Realizando comparaciones...")
    
    # Comparaciones OMG
    # 1. RUTs de OMG en Carga que coinciden con BICE OMG
    omg_coincidencias = ruts_carga_omg & ruts_bice_omg
    
    # 2. RUTs de OMG en Carga que NO están en BICE OMG
    omg_carga_no_en_bice = ruts_carga_omg - ruts_bice_omg
    
    # 3. RUTs en BICE OMG que NO están en Carga OMG
    omg_bice_no_en_carga = ruts_bice_omg - ruts_carga_omg
    
    # Comparaciones Pyme
    # 4. RUTs de Pyme en Carga que coinciden con BICE Pyme
    pyme_coincidencias = ruts_carga_pyme & ruts_bice_pyme
    
    # 5. RUTs de Pyme en Carga que NO están en BICE Pyme
    pyme_carga_no_en_bice = ruts_carga_pyme - ruts_bice_pyme
    
    # 6. RUTs en BICE Pyme que NO están en Carga Pyme
    pyme_bice_no_en_carga = ruts_bice_pyme - ruts_carga_pyme
    
    # Errores de clasificación
    # 7. RUTs de Pyme en Carga que aparecen en BICE OMG (error)
    pyme_en_bice_omg = ruts_carga_pyme & ruts_bice_omg
    
    # 8. RUTs de OMG en Carga que aparecen en BICE Pyme (error)
    omg_en_bice_pyme = ruts_carga_omg & ruts_bice_pyme
    
    print("\n" + "="*80)
    print("📊 RESULTADOS DE LA COMPARACIÓN")
    print("="*80)
    
    print(f"\n✅ COINCIDENCIAS:")
    print(f"  - OMG (Carga OMG = BICE OMG): {len(omg_coincidencias)}")
    print(f"  - Pyme (Carga Pyme = BICE Pyme): {len(pyme_coincidencias)}")
    print(f"  - TOTAL COINCIDENCIAS: {len(omg_coincidencias) + len(pyme_coincidencias)}")
    
    print(f"\n⚠️  INCONSISTENCIAS:")
    print(f"  OMG:")
    print(f"    1. RUTs OMG en Carga pero NO en BICE OMG: {len(omg_carga_no_en_bice)}")
    print(f"    2. RUTs en BICE OMG pero NO en Carga OMG: {len(omg_bice_no_en_carga)}")
    print(f"  Pyme:")
    print(f"    3. RUTs Pyme en Carga pero NO en BICE Pyme: {len(pyme_carga_no_en_bice)}")
    print(f"    4. RUTs en BICE Pyme pero NO en Carga Pyme: {len(pyme_bice_no_en_carga)}")
    print(f"  Errores de clasificación:")
    print(f"    5. RUTs Pyme en Carga que aparecen en BICE OMG: {len(pyme_en_bice_omg)}")
    print(f"    6. RUTs OMG en Carga que aparecen en BICE Pyme: {len(omg_en_bice_pyme)}")
    
    # Crear DataFrames de resultados
    resultados = []
    
    # 1. Coincidencias OMG
    for rut in omg_coincidencias:
        reg_carga = df_carga_omg[df_carga_omg['RUT_NORM'] == rut].iloc[0]
        reg_bice = df_bice_omg[df_bice_omg['RUT_NORM'] == rut].iloc[0]
        
        resultados.append({
            'RUT': rut,
            'ESTADO': 'COINCIDENCIA_OMG',
            'TIPO': 'OMG',
            'EMPRESA_CARGA': reg_carga.get('NOMBRE_CONTRATANTE', ''),
            'NOMBRE_CARGA': reg_carga.get('NOMBRE CARGA', ''),
            'NOMBRE_BICE': reg_bice.get('Nombre', ''),
            'APELLIDO_BICE': reg_bice.get('Apellido', ''),
            'EMAIL_BICE': reg_bice.get('Email', ''),
            'OBSERVACION': 'OK - RUT OMG presente en ambos archivos'
        })
    
    # 2. Coincidencias Pyme
    for rut in pyme_coincidencias:
        reg_carga = df_carga_pyme[df_carga_pyme['RUT_NORM'] == rut].iloc[0]
        reg_bice = df_bice_pyme[df_bice_pyme['RUT_NORM'] == rut].iloc[0]
        
        resultados.append({
            'RUT': rut,
            'ESTADO': 'COINCIDENCIA_PYME',
            'TIPO': 'PYME',
            'EMPRESA_CARGA': reg_carga.get('NOMBRE_CONTRATANTE', ''),
            'NOMBRE_CARGA': reg_carga.get('NOMBRE CARGA', ''),
            'NOMBRE_BICE': reg_bice.get('Nombre', ''),
            'APELLIDO_BICE': reg_bice.get('Apellido', ''),
            'EMAIL_BICE': reg_bice.get('Email', ''),
            'OBSERVACION': 'OK - RUT Pyme presente en ambos archivos'
        })
    
    # 3. OMG en Carga pero no en BICE
    for rut in omg_carga_no_en_bice:
        reg_carga = df_carga_omg[df_carga_omg['RUT_NORM'] == rut].iloc[0]
        
        resultados.append({
            'RUT': rut,
            'ESTADO': 'CARGA_OMG_SIN_BICE',
            'TIPO': 'OMG',
            'EMPRESA_CARGA': reg_carga.get('NOMBRE_CONTRATANTE', ''),
            'NOMBRE_CARGA': reg_carga.get('NOMBRE CARGA', ''),
            'NOMBRE_BICE': '',
            'APELLIDO_BICE': '',
            'EMAIL_BICE': '',
            'OBSERVACION': 'FALTA - RUT OMG en Carga pero NO en BICE OMG'
        })
    
    # 4. OMG en BICE pero no en Carga
    for rut in omg_bice_no_en_carga:
        reg_bice = df_bice_omg[df_bice_omg['RUT_NORM'] == rut].iloc[0]
        
        resultados.append({
            'RUT': rut,
            'ESTADO': 'BICE_OMG_SIN_CARGA',
            'TIPO': 'OMG',
            'EMPRESA_CARGA': '',
            'NOMBRE_CARGA': '',
            'NOMBRE_BICE': reg_bice.get('Nombre', ''),
            'APELLIDO_BICE': reg_bice.get('Apellido', ''),
            'EMAIL_BICE': reg_bice.get('Email', ''),
            'OBSERVACION': 'EXTRA - RUT en BICE OMG pero NO en Carga OMG'
        })
    
    # 5. Pyme en Carga pero no en BICE
    for rut in pyme_carga_no_en_bice:
        reg_carga = df_carga_pyme[df_carga_pyme['RUT_NORM'] == rut].iloc[0]
        
        resultados.append({
            'RUT': rut,
            'ESTADO': 'CARGA_PYME_SIN_BICE',
            'TIPO': 'PYME',
            'EMPRESA_CARGA': reg_carga.get('NOMBRE_CONTRATANTE', ''),
            'NOMBRE_CARGA': reg_carga.get('NOMBRE CARGA', ''),
            'NOMBRE_BICE': '',
            'APELLIDO_BICE': '',
            'EMAIL_BICE': '',
            'OBSERVACION': 'FALTA - RUT Pyme en Carga pero NO en BICE Pyme'
        })
    
    # 6. Pyme en BICE pero no en Carga
    for rut in pyme_bice_no_en_carga:
        reg_bice = df_bice_pyme[df_bice_pyme['RUT_NORM'] == rut].iloc[0]
        
        resultados.append({
            'RUT': rut,
            'ESTADO': 'BICE_PYME_SIN_CARGA',
            'TIPO': 'PYME',
            'EMPRESA_CARGA': '',
            'NOMBRE_CARGA': '',
            'NOMBRE_BICE': reg_bice.get('Nombre', ''),
            'APELLIDO_BICE': reg_bice.get('Apellido', ''),
            'EMAIL_BICE': reg_bice.get('Email', ''),
            'OBSERVACION': 'EXTRA - RUT en BICE Pyme pero NO en Carga Pyme'
        })
    
    # 7. Error: Pyme en Carga pero en BICE OMG
    for rut in pyme_en_bice_omg:
        reg_carga = df_carga_pyme[df_carga_pyme['RUT_NORM'] == rut].iloc[0]
        reg_bice = df_bice_omg[df_bice_omg['RUT_NORM'] == rut].iloc[0]
        
        resultados.append({
            'RUT': rut,
            'ESTADO': 'ERROR_PYME_EN_OMG',
            'TIPO': 'ERROR',
            'EMPRESA_CARGA': reg_carga.get('NOMBRE_CONTRATANTE', ''),
            'NOMBRE_CARGA': reg_carga.get('NOMBRE CARGA', ''),
            'NOMBRE_BICE': reg_bice.get('Nombre', ''),
            'APELLIDO_BICE': reg_bice.get('Apellido', ''),
            'EMAIL_BICE': reg_bice.get('Email', ''),
            'OBSERVACION': 'ERROR - RUT clasificado como Pyme en Carga pero está en BICE OMG'
        })
    
    # 8. Error: OMG en Carga pero en BICE Pyme
    for rut in omg_en_bice_pyme:
        reg_carga = df_carga_omg[df_carga_omg['RUT_NORM'] == rut].iloc[0]
        reg_bice = df_bice_pyme[df_bice_pyme['RUT_NORM'] == rut].iloc[0]
        
        resultados.append({
            'RUT': rut,
            'ESTADO': 'ERROR_OMG_EN_PYME',
            'TIPO': 'ERROR',
            'EMPRESA_CARGA': reg_carga.get('NOMBRE_CONTRATANTE', ''),
            'NOMBRE_CARGA': reg_carga.get('NOMBRE CARGA', ''),
            'NOMBRE_BICE': reg_bice.get('Nombre', ''),
            'APELLIDO_BICE': reg_bice.get('Apellido', ''),
            'EMAIL_BICE': reg_bice.get('Email', ''),
            'OBSERVACION': 'ERROR - RUT clasificado como OMG en Carga pero está en BICE Pyme'
        })
    
    # Crear DataFrame y guardar
    df_resultados = pd.DataFrame(resultados)
    
    # Ordenar por estado y RUT
    orden_estados = {
        'COINCIDENCIA_OMG': 1, 
        'COINCIDENCIA_PYME': 2, 
        'CARGA_OMG_SIN_BICE': 3, 
        'CARGA_PYME_SIN_BICE': 4,
        'BICE_OMG_SIN_CARGA': 5, 
        'BICE_PYME_SIN_CARGA': 6,
        'ERROR_PYME_EN_OMG': 7, 
        'ERROR_OMG_EN_PYME': 8
    }
    df_resultados['ORDEN'] = df_resultados['ESTADO'].map(orden_estados)
    df_resultados = df_resultados.sort_values(['ORDEN', 'RUT']).drop('ORDEN', axis=1)
    
    # Separar en dos DataFrames: coincidencias e inconsistencias
    df_coincidencias = df_resultados[df_resultados['ESTADO'].str.contains('COINCIDENCIA')].copy()
    df_inconsistencias = df_resultados[~df_resultados['ESTADO'].str.contains('COINCIDENCIA')].copy()
    
    # Guardar resultados
    resultado_dir = os.path.join(script_dir, 'resultado')
    os.makedirs(resultado_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Guardar archivo de coincidencias
    archivo_coincidencias = os.path.join(resultado_dir, f'comparacion_coincidencias_{timestamp}.xlsx')
    df_coincidencias.to_excel(archivo_coincidencias, index=False)
    
    # Guardar archivo de inconsistencias
    archivo_inconsistencias = os.path.join(resultado_dir, f'comparacion_inconsistencias_{timestamp}.xlsx')
    df_inconsistencias.to_excel(archivo_inconsistencias, index=False)
    
    print(f"\n💾 Resultados guardados en:")
    print(f"   📗 Coincidencias: {os.path.basename(archivo_coincidencias)}")
    print(f"   📕 Inconsistencias: {os.path.basename(archivo_inconsistencias)}")
    
    # Resumen por estado
    print("\n📋 Resumen por estado:")
    print(f"   ✅ COINCIDENCIAS: {len(df_coincidencias)}")
    if len(df_coincidencias) > 0:
        for estado, cantidad in df_coincidencias['ESTADO'].value_counts().items():
            print(f"      - {estado}: {cantidad}")
    
    print(f"   ⚠️  INCONSISTENCIAS: {len(df_inconsistencias)}")
    if len(df_inconsistencias) > 0:
        for estado, cantidad in df_inconsistencias['ESTADO'].value_counts().items():
            print(f"      - {estado}: {cantidad}")
    
    # Mostrar muestras
    if len(df_inconsistencias) > 0:
        print(f"\n🔍 Muestra de inconsistencias (primeros 10):")
        print(df_inconsistencias.head(10)[['RUT', 'ESTADO', 'TIPO', 'EMPRESA_CARGA', 'NOMBRE_BICE', 'APELLIDO_BICE']].to_string(index=False))
    
    print("\n" + "="*80)
    print("✅ Proceso completado")
    print("="*80)


if __name__ == "__main__":
    comparar_pyme_bice()
