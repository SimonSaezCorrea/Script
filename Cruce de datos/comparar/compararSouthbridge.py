"""
Script para comparar datos entre archivos de altas Cencosud + Mercer y archivo BICE Southbridge.

Compara RUTs y reporta inconsistencias considerando ambas empresas.

Archivos esperados en carpeta `data/Southbridge`:
- Altas SOAP al31012026-CENCOSUD.xlsx (CARGA Cencosud - Altas a agregar)
- Altas SOAP al31012026-MERCER.xlsx (CARGA Mercer - Altas a agregar)
- Southbridge_users_03_02_2026.xlsx (BICE - Usuarios existentes de ambas empresas)
"""
import pandas as pd
import os
import sys
from datetime import datetime

# Agregar la carpeta padre al path para poder importar utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.comparadores import (
    normalizar_rut_comparacion,
    filtrar_activos,
    separar_y_guardar_resultados,
    imprimir_resumen
)
from utils.normalizers import combinar_rut_dv, normalizar_nombre

# Constants for column names
NOMBRE_PROPIETARIO = 'Nombre propietario'
APELLIDO_PATERNO_PROPIETARIO = 'Apellido paterno propietario'
APELLIDO_MATERNO_PROPIETARIO = 'Apellido materno propietario'
EMAIL_PROPIETARIO = 'Email propietario'


def normalizar_ruts_dataframe_southbridge(df, col_rut, col_dv=None):
    """
    Normaliza RUTs en un DataFrame para comparación.
    Si tiene columna de DV separada, las combina primero.
    """
    if col_dv and col_dv in df.columns:
        # Combinar RUT + DV
        df['RUT_COMPLETO'] = df.apply(lambda row: combinar_rut_dv(row.get(col_rut, ''), row.get(col_dv, '')), axis=1)
        col_a_normalizar = 'RUT_COMPLETO'
    else:
        col_a_normalizar = col_rut
    
    # Normalizar RUTs
    df['RUT_NORM'] = df[col_a_normalizar].apply(normalizar_rut_comparacion)
    
    # Filtrar solo RUTs válidos
    df = df[df['RUT_NORM'].notna() & (df['RUT_NORM'] != '')].copy()
    
    # Crear columna RUT limpia (sin puntos ni guiones) para mostrar
    df['RUT'] = df['RUT_NORM']
    
    return df


def comparar_southbridge():
    """
    Compara los RUTs entre los archivos de altas (Cencosud + Mercer) y el archivo BICE de Southbridge.
    """
    # Rutas de archivos
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, 'data', 'Southbridge')
    
    # Buscar archivos dinámicamente
    archivo_carga_cencosud = None
    archivo_carga_mercer = None
    archivo_bice = None
    
    if not os.path.exists(data_dir):
        print(f"❌ Error: no existe la carpeta de datos: {data_dir}")
        return
    
    for filename in os.listdir(data_dir):
        # Ignorar archivos temporales de Excel
        if filename.startswith('~$'):
            continue
        
        if 'Altas SOAP' in filename and 'CENCOSUD' in filename:
            archivo_carga_cencosud = os.path.join(data_dir, filename)
        elif 'Altas SOAP' in filename and 'MERCER' in filename:
            archivo_carga_mercer = os.path.join(data_dir, filename)
        elif 'Southbridge_users' in filename:
            archivo_bice = os.path.join(data_dir, filename)
    
    if not archivo_carga_cencosud or not archivo_carga_mercer or not archivo_bice:
        print("❌ Error: No se encontraron todos los archivos necesarios")
        print(f"   Altas Cencosud: {archivo_carga_cencosud is not None}")
        print(f"   Altas Mercer: {archivo_carga_mercer is not None}")
        print(f"   BICE Southbridge: {archivo_bice is not None}")
        return
    
    print("="*80)
    print("📊 COMPARACIÓN ALTAS (CENCOSUD + MERCER) vs BICE - SOUTHBRIDGE")
    print("="*80)
    print(f"\nArchivo Altas Cencosud: {os.path.basename(archivo_carga_cencosud)}")
    print(f"Archivo Altas Mercer: {os.path.basename(archivo_carga_mercer)}")
    print(f"Archivo BICE: {os.path.basename(archivo_bice)}")
    
    # Leer archivos
    print("\n🔄 Leyendo archivos...")
    
    # Leer Altas Cencosud
    try:
        df_carga_cencosud = pd.read_excel(archivo_carga_cencosud)
        print("  ✓ Archivo Altas Cencosud leído correctamente")
    except Exception as e:
        print(f"  ❌ Error al leer archivo de altas Cencosud: {e}")
        return
    
    # Leer Altas Mercer
    try:
        df_carga_mercer = pd.read_excel(archivo_carga_mercer)
        print("  ✓ Archivo Altas Mercer leído correctamente")
    except Exception as e:
        print(f"  ❌ Error al leer archivo de altas Mercer: {e}")
        return
    
    # Leer BICE
    try:
        df_bice = pd.read_excel(archivo_bice)
        print("  ✓ Archivo BICE leído correctamente")
    except Exception as e:
        print(f"  ❌ Error al leer archivo BICE: {e}")
        return
    
    print("\n📈 Registros totales:")
    print(f"  - Altas Cencosud (total): {len(df_carga_cencosud)}")
    print(f"  - Altas Mercer (total): {len(df_carga_mercer)}")
    print(f"  - BICE (total): {len(df_bice)}")
    
    # Filtrar solo registros con Estado póliza = "Aprobado" en archivos de Altas
    total_cencosud = len(df_carga_cencosud)
    if 'Estado póliza' in df_carga_cencosud.columns:
        df_carga_cencosud['Estado póliza'] = df_carga_cencosud['Estado póliza'].astype(str).str.upper().str.strip()
        df_carga_cencosud = df_carga_cencosud[df_carga_cencosud['Estado póliza'] == 'APROBADO'].copy()
        print(f"  - Altas Cencosud (aprobadas): {len(df_carga_cencosud)} ({total_cencosud - len(df_carga_cencosud)} no aprobadas filtradas)")
    
    total_mercer = len(df_carga_mercer)
    if 'Estado póliza' in df_carga_mercer.columns:
        df_carga_mercer['Estado póliza'] = df_carga_mercer['Estado póliza'].astype(str).str.upper().str.strip()
        df_carga_mercer = df_carga_mercer[df_carga_mercer['Estado póliza'] == 'APROBADO'].copy()
        print(f"  - Altas Mercer (aprobadas): {len(df_carga_mercer)} ({total_mercer - len(df_carga_mercer)} no aprobadas filtradas)")
    
    # Filtrar solo registros activos en BICE
    total_bice = len(df_bice)
    if 'Estado' in df_bice.columns:
        df_bice = filtrar_activos(df_bice, 'Estado')
        print(f"  - BICE (activos): {len(df_bice)} ({total_bice - len(df_bice)} inactivos filtrados)")
    
    # Procesar RUTs
    print("\n🔧 Procesando RUTs...")
    
    # Normalizar RUTs en archivos de Altas (RUT + DV separados)
    df_carga_cencosud = normalizar_ruts_dataframe_southbridge(df_carga_cencosud, 'Rut propietario', 'Propietario DV')
    df_carga_mercer = normalizar_ruts_dataframe_southbridge(df_carga_mercer, 'Rut propietario', 'Propietario DV')
    
    # Normalizar RUTs en archivo BICE
    df_bice = normalizar_ruts_dataframe_southbridge(df_bice, 'RUT')
    
    print(f"  ✓ RUTs válidos: Cencosud={len(df_carga_cencosud)}, Mercer={len(df_carga_mercer)}, BICE={len(df_bice)}")
    
    # Obtener sets de RUTs únicos
    ruts_cencosud = set(df_carga_cencosud['RUT_NORM'].unique())
    ruts_mercer = set(df_carga_mercer['RUT_NORM'].unique())
    ruts_bice = set(df_bice['RUT_NORM'].unique())
    
    # Combinar RUTs de ambas cargas
    ruts_carga_total = ruts_cencosud | ruts_mercer
    
    print("\n🔢 RUTs únicos:")
    print(f"  - Altas Cencosud: {len(ruts_cencosud)}")
    print(f"  - Altas Mercer: {len(ruts_mercer)}")
    print(f"  - Altas Total (Cencosud + Mercer): {len(ruts_carga_total)}")
    print(f"  - BICE: {len(ruts_bice)}")
    
    # Realizar comparaciones
    print("\n🔍 Realizando comparaciones...")
    
    # 1. Coincidencias
    coincidencias_cencosud = ruts_cencosud & ruts_bice
    coincidencias_mercer = ruts_mercer & ruts_bice
    
    # 2. En Carga pero no en BICE
    cencosud_sin_bice = ruts_cencosud - ruts_bice
    mercer_sin_bice = ruts_mercer - ruts_bice
    
    # 3. En BICE pero no en ninguna carga (IMPORTANTE: revisar)
    bice_sin_ninguna_carga = ruts_bice - ruts_carga_total
    
    print("\n" + "="*80)
    print("📊 RESULTADOS DE LA COMPARACIÓN")
    print("="*80)
    
    print("\n✅ COINCIDENCIAS:")
    print(f"  - Cencosud: {len(coincidencias_cencosud)}")
    print(f"  - Mercer: {len(coincidencias_mercer)}")
    print(f"  - Total: {len(coincidencias_cencosud | coincidencias_mercer)}")
    
    print("\n⚠️  INCONSISTENCIAS:")
    print(f"  1. RUTs en Altas Cencosud pero NO en BICE: {len(cencosud_sin_bice)}")
    print(f"  2. RUTs en Altas Mercer pero NO en BICE: {len(mercer_sin_bice)}")
    print(f"  3. ⚠️  RUTs en BICE pero NO en ninguna Carga: {len(bice_sin_ninguna_carga)} (PONER OJO)")
    
    # Crear DataFrames de resultados
    resultados = []
    
    # 1. Coincidencias Cencosud
    for rut in coincidencias_cencosud:
        reg_carga = df_carga_cencosud[df_carga_cencosud['RUT_NORM'] == rut].iloc[0]
        reg_bice = df_bice[df_bice['RUT_NORM'] == rut].iloc[0]
        cantidad_carga = len(df_carga_cencosud[df_carga_cencosud['RUT_NORM'] == rut])
        cantidad_bice = len(df_bice[df_bice['RUT_NORM'] == rut])
        
        # Normalizar nombres y apellidos
        nombre_carga = normalizar_nombre(reg_carga.get(NOMBRE_PROPIETARIO, ''))
        apellido_pat = normalizar_nombre(reg_carga.get(APELLIDO_PATERNO_PROPIETARIO, ''))
        apellido_mat = normalizar_nombre(reg_carga.get(APELLIDO_MATERNO_PROPIETARIO, ''))
        apellidos_carga = f"{apellido_pat} {apellido_mat}".strip()
        nombre_bice = normalizar_nombre(reg_bice.get('Nombre', ''))
        apellido_bice = normalizar_nombre(reg_bice.get('Apellido', ''))
        
        estado = 'DIFERENCIA_CANTIDAD_CENCOSUD' if cantidad_carga != cantidad_bice else 'COINCIDENCIA_CENCOSUD'
        
        resultados.append({
            'RUT': rut,
            'ESTADO': estado,
            'TIPO': 'CENCOSUD',
            'NOMBRE_CARGA': nombre_carga,
            'APELLIDOS_CARGA': apellidos_carga,
            'NOMBRE_BICE': nombre_bice,
            'APELLIDO_BICE': apellido_bice,
            'EMAIL_CARGA': reg_carga.get(EMAIL_PROPIETARIO, ''),
            'EMAIL_BICE': reg_bice.get('Email', ''),
            'CANTIDAD_CARGA': cantidad_carga,
            'CANTIDAD_BICE': cantidad_bice,
            'OBSERVACION': 'OK - RUT presente en ambos archivos' if estado == 'COINCIDENCIA_CENCOSUD' else f'DIFERENCIA - Carga tiene {cantidad_carga}, BICE tiene {cantidad_bice}'
        })
    
    # 2. Coincidencias Mercer
    for rut in coincidencias_mercer:
        reg_carga = df_carga_mercer[df_carga_mercer['RUT_NORM'] == rut].iloc[0]
        reg_bice = df_bice[df_bice['RUT_NORM'] == rut].iloc[0]
        cantidad_carga = len(df_carga_mercer[df_carga_mercer['RUT_NORM'] == rut])
        cantidad_bice = len(df_bice[df_bice['RUT_NORM'] == rut])
        
        # Normalizar nombres y apellidos
        nombre_carga = normalizar_nombre(reg_carga.get(NOMBRE_PROPIETARIO, ''))
        apellido_pat = normalizar_nombre(reg_carga.get(APELLIDO_PATERNO_PROPIETARIO, ''))
        apellido_mat = normalizar_nombre(reg_carga.get(APELLIDO_MATERNO_PROPIETARIO, ''))
        apellidos_carga = f"{apellido_pat} {apellido_mat}".strip()
        nombre_bice = normalizar_nombre(reg_bice.get('Nombre', ''))
        apellido_bice = normalizar_nombre(reg_bice.get('Apellido', ''))
        
        estado = 'DIFERENCIA_CANTIDAD_MERCER' if cantidad_carga != cantidad_bice else 'COINCIDENCIA_MERCER'
        
        resultados.append({
            'RUT': rut,
            'ESTADO': estado,
            'TIPO': 'MERCER',
            'NOMBRE_CARGA': nombre_carga,
            'APELLIDOS_CARGA': apellidos_carga,
            'NOMBRE_BICE': nombre_bice,
            'APELLIDO_BICE': apellido_bice,
            'EMAIL_CARGA': reg_carga.get(EMAIL_PROPIETARIO, ''),
            'EMAIL_BICE': reg_bice.get('Email', ''),
            'CANTIDAD_CARGA': cantidad_carga,
            'CANTIDAD_BICE': cantidad_bice,
            'OBSERVACION': 'OK - RUT presente en ambos archivos' if estado == 'COINCIDENCIA_MERCER' else f'DIFERENCIA - Carga tiene {cantidad_carga}, BICE tiene {cantidad_bice}'
        })
    
    # 3. En Cencosud pero no en BICE (HAY QUE AGREGAR)
    for rut in cencosud_sin_bice:
        reg_carga = df_carga_cencosud[df_carga_cencosud['RUT_NORM'] == rut].iloc[0]
        
        # Normalizar nombres y apellidos
        nombre_carga = normalizar_nombre(reg_carga.get(NOMBRE_PROPIETARIO, ''))
        apellido_pat = normalizar_nombre(reg_carga.get(APELLIDO_PATERNO_PROPIETARIO, ''))
        apellido_mat = normalizar_nombre(reg_carga.get(APELLIDO_MATERNO_PROPIETARIO, ''))
        apellidos_carga = f"{apellido_pat} {apellido_mat}".strip()
        
        resultados.append({
            'RUT': rut,
            'ESTADO': 'CARGA_CENCOSUD_SIN_BICE',
            'TIPO': 'CENCOSUD',
            'NOMBRE_CARGA': nombre_carga,
            'APELLIDOS_CARGA': apellidos_carga,
            'NOMBRE_BICE': '',
            'APELLIDO_BICE': '',
            'EMAIL_CARGA': reg_carga.get(EMAIL_PROPIETARIO, ''),
            'EMAIL_BICE': '',
            'CANTIDAD_CARGA': len(df_carga_cencosud[df_carga_cencosud['RUT_NORM'] == rut]),
            'CANTIDAD_BICE': 0,
            'OBSERVACION': 'FALTA - RUT en Altas Cencosud pero NO en BICE (hay que agregar)'
        })
    
    # 4. En Mercer pero no en BICE (HAY QUE AGREGAR)
    for rut in mercer_sin_bice:
        reg_carga = df_carga_mercer[df_carga_mercer['RUT_NORM'] == rut].iloc[0]
        
        # Normalizar nombres y apellidos
        nombre_carga = normalizar_nombre(reg_carga.get(NOMBRE_PROPIETARIO, ''))
        apellido_pat = normalizar_nombre(reg_carga.get(APELLIDO_PATERNO_PROPIETARIO, ''))
        apellido_mat = normalizar_nombre(reg_carga.get(APELLIDO_MATERNO_PROPIETARIO, ''))
        apellidos_carga = f"{apellido_pat} {apellido_mat}".strip()
        
        resultados.append({
            'RUT': rut,
            'ESTADO': 'CARGA_MERCER_SIN_BICE',
            'TIPO': 'MERCER',
            'NOMBRE_CARGA': nombre_carga,
            'APELLIDOS_CARGA': apellidos_carga,
            'NOMBRE_BICE': '',
            'APELLIDO_BICE': '',
            'EMAIL_CARGA': reg_carga.get(EMAIL_PROPIETARIO, ''),
            'EMAIL_BICE': '',
            'CANTIDAD_CARGA': len(df_carga_mercer[df_carga_mercer['RUT_NORM'] == rut]),
            'CANTIDAD_BICE': 0,
            'OBSERVACION': 'FALTA - RUT en Altas Mercer pero NO en BICE (hay que agregar)'
        })
    
    # 5. En BICE pero no en ninguna carga (PONER OJO)
    for rut in bice_sin_ninguna_carga:
        reg_bice = df_bice[df_bice['RUT_NORM'] == rut].iloc[0]
        
        # Normalizar nombres y apellidos
        nombre_bice = normalizar_nombre(reg_bice.get('Nombre', ''))
        apellido_bice = normalizar_nombre(reg_bice.get('Apellido', ''))
        
        resultados.append({
            'RUT': rut,
            'ESTADO': 'BICE_SIN_NINGUNA_CARGA',
            'TIPO': 'SOUTHBRIDGE',
            'NOMBRE_CARGA': '',
            'APELLIDOS_CARGA': '',
            'NOMBRE_BICE': nombre_bice,
            'APELLIDO_BICE': apellido_bice,
            'EMAIL_CARGA': '',
            'EMAIL_BICE': reg_bice.get('Email', ''),
            'CANTIDAD_CARGA': 0,
            'CANTIDAD_BICE': len(df_bice[df_bice['RUT_NORM'] == rut]),
            'OBSERVACION': '⚠️ PONER OJO - RUT en BICE pero NO en ninguna Altas (ni Cencosud ni Mercer)'
        })
    
    # Crear DataFrame y guardar
    df_resultados = pd.DataFrame(resultados)
    
    # Orden de estados
    orden_estados = {
        'COINCIDENCIA_CENCOSUD': 1,
        'COINCIDENCIA_MERCER': 2,
        'DIFERENCIA_CANTIDAD_CENCOSUD': 3,
        'DIFERENCIA_CANTIDAD_MERCER': 4,
        'CARGA_CENCOSUD_SIN_BICE': 5,
        'CARGA_MERCER_SIN_BICE': 6,
        'BICE_SIN_NINGUNA_CARGA': 7
    }
    
    # Usar función común para separar y guardar
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    df_coincidencias, df_inconsistencias, archivos = separar_y_guardar_resultados(
        df_resultados, script_dir, timestamp, orden_estados, prefijo='southbridge_'
    )
    
    # Imprimir resumen usando función común
    imprimir_resumen(df_coincidencias, df_inconsistencias, archivos)
    
    # Crear carpeta de resultado una sola vez
    resultado_dir = os.path.join(script_dir, 'resultado')
    os.makedirs(resultado_dir, exist_ok=True)

    # Generar CSV especial para registros en CARGA CENCOSUD que NO están en BICE
    df_cencosud_sin_bice = df_inconsistencias[df_inconsistencias['ESTADO'] == 'CARGA_CENCOSUD_SIN_BICE'].copy()
    if len(df_cencosud_sin_bice) > 0:
        df_csv_cencosud = pd.DataFrame({
            'Nombre': df_cencosud_sin_bice['NOMBRE_CARGA'],
            'Apellido': df_cencosud_sin_bice['APELLIDOS_CARGA'],
            'Email': df_cencosud_sin_bice['EMAIL_CARGA'],
            'RUT': df_cencosud_sin_bice['RUT']
        })
        
        from utils.file_handlers import guardar_csv_formato_especial
        archivo_csv_cencosud = os.path.join(resultado_dir, f'carga_sin_bice_cencosud_{timestamp}.csv')
        guardar_csv_formato_especial(df_csv_cencosud, archivo_csv_cencosud)
        print(f"   📄 Carga Cencosud sin BICE (hay que agregar): {os.path.basename(archivo_csv_cencosud)}")
    
    # Generar CSV especial para registros en CARGA MERCER que NO están en BICE
    df_mercer_sin_bice = df_inconsistencias[df_inconsistencias['ESTADO'] == 'CARGA_MERCER_SIN_BICE'].copy()
    if len(df_mercer_sin_bice) > 0:
        df_csv_mercer = pd.DataFrame({
            'Nombre': df_mercer_sin_bice['NOMBRE_CARGA'],
            'Apellido': df_mercer_sin_bice['APELLIDOS_CARGA'],
            'Email': df_mercer_sin_bice['EMAIL_CARGA'],
            'RUT': df_mercer_sin_bice['RUT']
        })
        
        from utils.file_handlers import guardar_csv_formato_especial
        archivo_csv_mercer = os.path.join(resultado_dir, f'carga_sin_bice_mercer_{timestamp}.csv')
        guardar_csv_formato_especial(df_csv_mercer, archivo_csv_mercer)
        print(f"   📄 Carga Mercer sin BICE (hay que agregar): {os.path.basename(archivo_csv_mercer)}")
    
    # Generar CSV especial para registros en BICE que NO están en ninguna carga (PONER OJO)
    df_bice_sin_carga = df_inconsistencias[df_inconsistencias['ESTADO'] == 'BICE_SIN_NINGUNA_CARGA'].copy()
    if len(df_bice_sin_carga) > 0:
        df_csv_bice = pd.DataFrame({
            'Nombre': df_bice_sin_carga['NOMBRE_BICE'],
            'Apellido': df_bice_sin_carga['APELLIDO_BICE'],
            'Email': df_bice_sin_carga['EMAIL_BICE'],
            'RUT': df_bice_sin_carga['RUT']
        })
        
        from utils.file_handlers import guardar_csv_formato_especial
        archivo_csv_bice = os.path.join(resultado_dir, f'bice_sin_ninguna_carga_southbridge_{timestamp}.csv')
        guardar_csv_formato_especial(df_csv_bice, archivo_csv_bice, solo_rut=True)
        print(f"   ⚠️  BICE sin ninguna Carga (PONER OJO): {os.path.basename(archivo_csv_bice)}")
    
    # Mostrar muestras
    if len(df_inconsistencias) > 0:
        print("\n🔍 Muestra de inconsistencias (primeros 10):")
        columnas_mostrar = ['RUT', 'ESTADO', 'TIPO', 'NOMBRE_CARGA', 'NOMBRE_BICE']
        print(df_inconsistencias.head(10)[columnas_mostrar].to_string(index=False))
    
    print("\n" + "="*80)
    print("✅ Proceso completado")
    print("="*80)


if __name__ == "__main__":
    comparar_southbridge()
