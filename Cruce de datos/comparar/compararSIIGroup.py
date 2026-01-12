"""
Script para comparar datos entre archivo de carga SII Group y archivo BICE SII Group.

Compara RUTs y reporta inconsistencias.

Archivos:
- Nómina PAWER Enero 2026 - SII Group Chile.xlsx (CARGA)
- SII Group_users_12_01_2026.xlsx (BICE)
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

def comparar_sii_group():
    """
    Compara los RUTs entre el archivo de carga y el archivo BICE de SII Group.
    """
    # Rutas de archivos
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, 'data', 'SII Group')
    
    # Buscar archivos dinámicamente
    archivo_carga = None
    archivo_bice = None
    
    for filename in os.listdir(data_dir):
        # Ignorar archivos temporales de Excel
        if filename.startswith('~$'):
            continue
            
        if 'Nómina PAWER' in filename and 'SII Group' in filename:
            archivo_carga = os.path.join(data_dir, filename)
        elif 'SII Group_users' in filename:
            archivo_bice = os.path.join(data_dir, filename)
    
    if not archivo_carga or not archivo_bice:
        print("❌ Error: No se encontraron todos los archivos necesarios")
        print(f"   Carga encontrado: {archivo_carga is not None}")
        print(f"   BICE encontrado: {archivo_bice is not None}")
        return
    
    print("="*80)
    print("📊 COMPARACIÓN CARGA vs BICE - SII GROUP")
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
    if 'Estado' in df_bice.columns:
        df_bice = filtrar_activos(df_bice, 'Estado')
        print(f"  - BICE (activos): {len(df_bice)}")
    
    # Procesar RUTs
    print("\n🔧 Procesando RUTs...")
    
    # Normalizar RUTs en ambos archivos
    df_carga = normalizar_ruts_dataframe(df_carga, 'RUT')
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
            'TIPO': 'SII_GROUP',
            'NOMBRE_CARGA': reg_carga.get('Nombre', ''),
            'NOMBRE_BICE': reg_bice.get('Nombre', ''),
            'EMAIL_CARGA': reg_carga.get('Correo', ''),
            'EMAIL_BICE': reg_bice.get('Correo', ''),
            'OBSERVACION': 'OK - RUT presente en ambos archivos'
        })
    
    # 2. En Carga pero no en BICE
    for rut in carga_no_en_bice:
        reg_carga = df_carga[df_carga['RUT_NORM'] == rut].iloc[0]
        
        resultados.append({
            'RUT': rut,
            'ESTADO': 'CARGA_SIN_BICE',
            'TIPO': 'SII_GROUP',
            'NOMBRE_CARGA': reg_carga.get('Nombre', ''),
            'NOMBRE_BICE': '',
            'EMAIL_CARGA': reg_carga.get('Correo', ''),
            'EMAIL_BICE': '',
            'OBSERVACION': 'FALTA - RUT en Carga pero NO en BICE'
        })
    
    # 3. En BICE pero no en Carga
    for rut in bice_no_en_carga:
        reg_bice = df_bice[df_bice['RUT_NORM'] == rut].iloc[0]
        
        resultados.append({
            'RUT': rut,
            'ESTADO': 'BICE_SIN_CARGA',
            'TIPO': 'SII_GROUP',
            'NOMBRE_CARGA': '',
            'NOMBRE_BICE': reg_bice.get('Nombre', ''),
            'EMAIL_CARGA': '',
            'EMAIL_BICE': reg_bice.get('Correo', ''),
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
        columnas_mostrar = ['RUT', 'ESTADO', 'NOMBRE_CARGA', 'NOMBRE_BICE']
        print(df_inconsistencias.head(10)[columnas_mostrar].to_string(index=False))
    
    print("\n" + "="*80)
    print("✅ Proceso completado")
    print("="*80)


if __name__ == "__main__":
    comparar_sii_group()
