"""
Script para comparar datos entre archivo de carga Sonda y archivo BICE Sonda.

Compara RUTs y reporta inconsistencias.

Archivos:
- Nomina Beneficio Seg Mascotas Pawer Dic 25- Sonda.xlsx (CARGA)
- Sonda_users_12_01_2026.xlsx (BICE)
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
    normalizar_ruts_dataframe,
    separar_y_guardar_resultados,
    imprimir_resumen
)


def comparar_sonda():
    """
    Compara los RUTs entre el archivo de carga y el archivo BICE de Sonda.
    """
    # Rutas de archivos
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, 'data', 'Sonda')
    
    # Buscar archivos dinámicamente
    archivo_carga = None
    archivo_bice = None
    
    for filename in os.listdir(data_dir):
        # Ignorar archivos temporales de Excel
        if filename.startswith('~$'):
            continue
            
        if 'Nomina' in filename and 'Sonda' in filename:
            archivo_carga = os.path.join(data_dir, filename)
        elif 'Sonda_users' in filename:
            archivo_bice = os.path.join(data_dir, filename)
    
    if not archivo_carga or not archivo_bice:
        print("❌ Error: No se encontraron todos los archivos necesarios")
        print(f"   Carga encontrado: {archivo_carga is not None}")
        print(f"   BICE encontrado: {archivo_bice is not None}")
        return
    
    print("="*80)
    print("📊 COMPARACIÓN CARGA vs BICE - SONDA")
    print("="*80)
    print(f"\nArchivo Carga: {os.path.basename(archivo_carga)}")
    print(f"Archivo BICE: {os.path.basename(archivo_bice)}")
    
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
    
    # Leer BICE (Excel)
    df_bice = pd.read_excel(archivo_bice)
    print(f"  ✓ Archivo BICE leído correctamente")
    
    print(f"\n📈 Registros totales:")
    print(f"  - Carga: {len(df_carga)}")
    print(f"  - BICE (total): {len(df_bice)}")
    
    # Filtrar solo registros con Estado = VERDADERO en archivo BICE
    total_bice = len(df_bice)
    if 'Estado' in df_bice.columns:
        df_bice = filtrar_activos(df_bice, 'Estado')
        print(f"  - BICE (activos): {len(df_bice)}")
        print(f"\n🔍 Filtrando registros activos (Estado = VERDADERO)...")
        print(f"  ✓ BICE: {len(df_bice)} activos de {total_bice} totales ({total_bice - len(df_bice)} inactivos filtrados)")
    
    # Procesar RUTs
    print("\n🔧 Procesando RUTs...")
    
    # Normalizar RUTs en ambos archivos
    df_carga = normalizar_ruts_dataframe(df_carga, 'Rut')
    df_bice = normalizar_ruts_dataframe(df_bice, 'RUT')
    
    print(f"  ✓ RUTs válidos: Carga={len(df_carga)}, BICE={len(df_bice)}")
    
    # Obtener sets de RUTs únicos
    ruts_carga = set(df_carga['RUT_NORM'].unique())
    ruts_bice = set(df_bice['RUT_NORM'].unique())
    
    print(f"\n🔢 RUTs únicos:")
    print(f"  - Carga: {len(ruts_carga)}")
    print(f"  - BICE: {len(ruts_bice)}")
    
    # Realizar comparaciones
    print("\n🔍 Realizando comparaciones...")
    
    # 1. RUTs que coinciden
    coincidencias = ruts_carga & ruts_bice
    
    # 2. RUTs en Carga que NO están en BICE
    carga_no_en_bice = ruts_carga - ruts_bice
    
    # 3. RUTs en BICE que NO están en Carga
    bice_no_en_carga = ruts_bice - ruts_carga
    
    print("\n" + "="*80)
    print("📊 RESULTADOS DE LA COMPARACIÓN")
    print("="*80)
    
    print(f"\n✅ COINCIDENCIAS: {len(coincidencias)}")
    print(f"\n⚠️  INCONSISTENCIAS:")
    print(f"  1. RUTs en Carga pero NO en BICE: {len(carga_no_en_bice)}")
    print(f"  2. RUTs en BICE pero NO en Carga: {len(bice_no_en_carga)}")
    
    # Crear DataFrames de resultados
    resultados = []
    
    # 1. Coincidencias
    for rut in coincidencias:
        reg_carga = df_carga[df_carga['RUT_NORM'] == rut].iloc[0]
        reg_bice = df_bice[df_bice['RUT_NORM'] == rut].iloc[0]
        
        resultados.append({
            'RUT': rut,
            'ESTADO': 'COINCIDENCIA',
            'TIPO': 'SONDA',
            'NOMBRES_CARGA': reg_carga.get('Nombres', ''),
            'APELLIDOS_CARGA': f"{reg_carga.get('Primer apellido', '')} {reg_carga.get('Segundo apellido', '')}".strip(),
            'NOMBRE_BICE': reg_bice.get('Nombre', ''),
            'APELLIDO_BICE': reg_bice.get('Apellido', ''),
            'EMAIL_CARGA': reg_carga.get('Correo electrónico', ''),
            'EMAIL_BICE': reg_bice.get('Email', ''),
            'OBSERVACION': 'OK - RUT presente en ambos archivos'
        })
    
    # 2. En Carga pero no en BICE
    for rut in carga_no_en_bice:
        reg_carga = df_carga[df_carga['RUT_NORM'] == rut].iloc[0]
        
        resultados.append({
            'RUT': rut,
            'ESTADO': 'CARGA_SIN_BICE',
            'TIPO': 'SONDA',
            'NOMBRES_CARGA': reg_carga.get('Nombres', ''),
            'APELLIDOS_CARGA': f"{reg_carga.get('Primer apellido', '')} {reg_carga.get('Segundo apellido', '')}".strip(),
            'NOMBRE_BICE': '',
            'APELLIDO_BICE': '',
            'EMAIL_CARGA': reg_carga.get('Correo electrónico', ''),
            'EMAIL_BICE': '',
            'OBSERVACION': 'FALTA - RUT en Carga pero NO en BICE'
        })
    
    # 3. En BICE pero no en Carga
    for rut in bice_no_en_carga:
        reg_bice = df_bice[df_bice['RUT_NORM'] == rut].iloc[0]
        
        resultados.append({
            'RUT': rut,
            'ESTADO': 'BICE_SIN_CARGA',
            'TIPO': 'SONDA',
            'NOMBRES_CARGA': '',
            'APELLIDOS_CARGA': '',
            'NOMBRE_BICE': reg_bice.get('Nombre', ''),
            'APELLIDO_BICE': reg_bice.get('Apellido', ''),
            'EMAIL_CARGA': '',
            'EMAIL_BICE': reg_bice.get('Email', ''),
            'OBSERVACION': 'EXTRA - RUT en BICE pero NO en Carga'
        })
    
    # Crear DataFrame y guardar
    df_resultados = pd.DataFrame(resultados)
    
    # Orden de estados
    orden_estados = {
        'COINCIDENCIA': 1,
        'CARGA_SIN_BICE': 2,
        'BICE_SIN_CARGA': 3
    }
    
    # Usar función común para separar y guardar
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    df_coincidencias, df_inconsistencias, archivos = separar_y_guardar_resultados(
        df_resultados, script_dir, timestamp, orden_estados
    )
    
    # Imprimir resumen usando función común
    imprimir_resumen(df_coincidencias, df_inconsistencias, archivos)
    
    # Mostrar muestras
    if len(df_inconsistencias) > 0:
        print(f"\n🔍 Muestra de inconsistencias (primeros 10):")
        columnas_mostrar = ['RUT', 'ESTADO', 'NOMBRES_CARGA', 'NOMBRE_BICE', 'APELLIDO_BICE']
        print(df_inconsistencias.head(10)[columnas_mostrar].to_string(index=False))
    
    print("\n" + "="*80)
    print("✅ Proceso completado")
    print("="*80)


if __name__ == "__main__":
    comparar_sonda()
