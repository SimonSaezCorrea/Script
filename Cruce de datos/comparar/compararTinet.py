"""
Script para comparar datos entre archivo de carga Tinet y archivo BICE Tinet.

Compara RUTs y reporta inconsistencias.

Archivos esperados en carpeta `data/Tinet`:
- Base de datos Tinet  - Pawer Nov 24.xlsx (CARGA)
- Tinet_users_13_01_2026.xlsx (BICE)
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


def comparar_tinet():
    """
    Compara los RUTs entre el archivo de carga y el archivo BICE de Tinet.
    """
    # Rutas de archivos
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, 'data', 'Tinet')

    # Buscar archivos dinámicamente
    archivo_carga = None
    archivo_bice = None

    if not os.path.exists(data_dir):
        print(f"❌ Error: no existe la carpeta de datos: {data_dir}")
        return

    for filename in os.listdir(data_dir):
        # Ignorar archivos temporales de Excel
        if filename.startswith('~$'):
            continue

        if 'Base de datos Tinet' in filename:
            archivo_carga = os.path.join(data_dir, filename)
        elif 'Tinet_users' in filename:
            archivo_bice = os.path.join(data_dir, filename)

    if not archivo_carga or not archivo_bice:
        print("❌ Error: No se encontraron todos los archivos necesarios")
        print(f"   Carga encontrado: {archivo_carga is not None}")
        print(f"   BICE encontrado: {archivo_bice is not None}")
        return

    print("="*80)
    print("📊 COMPARACIÓN CARGA vs BICE - TINET")
    print("="*80)
    print(f"\nArchivo Carga: {os.path.basename(archivo_carga)}")
    print(f"Archivo BICE: {os.path.basename(archivo_bice)}")

    # Leer archivos
    print("\n🔄 Leyendo archivos...")

    # Leer Carga (Excel)
    try:
        df_carga = pd.read_excel(archivo_carga)
        print(f"  ✓ Archivo Carga leído correctamente")
    except Exception as e:
        print(f"  ❌ Error al leer archivo de carga: {e}")
        return

    # Leer BICE (Excel)
    try:
        df_bice = pd.read_excel(archivo_bice)
        print(f"  ✓ Archivo BICE leído correctamente")
    except Exception as e:
        print(f"  ❌ Error al leer archivo BICE: {e}")
        return

    print(f"\n📈 Registros totales:")
    print(f"  - Carga: {len(df_carga)}")
    print(f"  - BICE (total): {len(df_bice)}")

    # Filtrar solo registros activos en BICE si existe columna 'Activo' o 'Estado'
    if 'Activo' in df_bice.columns:
        df_bice = filtrar_activos(df_bice, 'Activo')
        print(f"  - BICE (activos): {len(df_bice)}")
    elif 'Estado' in df_bice.columns:
        df_bice = filtrar_activos(df_bice, 'Estado')
        print(f"  - BICE (activos): {len(df_bice)}")

    # Procesar RUTs
    print("\n🔧 Procesando RUTs...")

    # Normalizar RUTs en ambos archivos
    df_carga = normalizar_ruts_dataframe(df_carga, 'RUT - DV')
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

    coincidencias = ruts_carga & ruts_bice
    carga_no_en_bice = ruts_carga - ruts_bice
    bice_no_en_carga = ruts_bice - ruts_carga

    # Detectar diferencias de cantidad
    print("\n🔢 Detectando diferencias de cantidad por RUT...")
    diferencias_cantidad = []
    for rut in coincidencias:
        cantidad_carga = len(df_carga[df_carga['RUT_NORM'] == rut])
        cantidad_bice = len(df_bice[df_bice['RUT_NORM'] == rut])
        if cantidad_carga != cantidad_bice:
            diferencias_cantidad.append({
                'rut': rut,
                'cantidad_carga': cantidad_carga,
                'cantidad_bice': cantidad_bice
            })

    print("\n" + "="*80)
    print("📊 RESULTADOS DE LA COMPARACIÓN")
    print("="*80)

    print(f"\n✅ COINCIDENCIAS: {len(coincidencias)}")
    print(f"\n⚠️  INCONSISTENCIAS:")
    print(f"  1. RUTs en Carga pero NO en BICE: {len(carga_no_en_bice)}")
    print(f"  2. RUTs en BICE pero NO en Carga: {len(bice_no_en_carga)}")
    print(f"  3. RUTs con diferente cantidad de registros: {len(diferencias_cantidad)}")

    resultados = []

    # 1. Coincidencias (con cantidad correcta)
    ruts_con_diferencia_cantidad = set([d['rut'] for d in diferencias_cantidad])
    for rut in coincidencias:
        if rut in ruts_con_diferencia_cantidad:
            continue  # Se procesarán después
        
        reg_carga = df_carga[df_carga['RUT_NORM'] == rut].iloc[0]
        reg_bice = df_bice[df_bice['RUT_NORM'] == rut].iloc[0]
        cantidad_carga = len(df_carga[df_carga['RUT_NORM'] == rut])
        cantidad_bice = len(df_bice[df_bice['RUT_NORM'] == rut])

        resultados.append({
            'RUT': rut,
            'ESTADO': 'COINCIDENCIA',
            'TIPO': 'TINET',
            'NOMBRES_CARGA': reg_carga.get('Nombre', ''),
            'APELLIDOS_CARGA': f"{reg_carga.get('Apellido Paterno', '')} {reg_carga.get('Apellido Materno', '')}".strip(),
            'NOMBRE_BICE': reg_bice.get('Nombre', ''),
            'APELLIDO_BICE': reg_bice.get('Apellido', ''),
            'EMAIL_CARGA': reg_carga.get('Correo Tinet', ''),
            'EMAIL_BICE': reg_bice.get('Email', '') or reg_bice.get('Correo', ''),
            'CANTIDAD_CARGA': cantidad_carga,
            'CANTIDAD_BICE': cantidad_bice,
            'OBSERVACION': 'OK - RUT presente en ambos archivos'
        })

    # 1b. Diferencias de cantidad
    for diff in diferencias_cantidad:
        rut = diff['rut']
        reg_carga = df_carga[df_carga['RUT_NORM'] == rut].iloc[0]
        reg_bice = df_bice[df_bice['RUT_NORM'] == rut].iloc[0]

        resultados.append({
            'RUT': rut,
            'ESTADO': 'DIFERENCIA_CANTIDAD',
            'TIPO': 'TINET',
            'NOMBRES_CARGA': reg_carga.get('Nombre', ''),
            'APELLIDOS_CARGA': f"{reg_carga.get('Apellido Paterno', '')} {reg_carga.get('Apellido Materno', '')}".strip(),
            'NOMBRE_BICE': reg_bice.get('Nombre', ''),
            'APELLIDO_BICE': reg_bice.get('Apellido', ''),
            'EMAIL_CARGA': reg_carga.get('Correo Tinet', ''),
            'EMAIL_BICE': reg_bice.get('Email', '') or reg_bice.get('Correo', ''),
            'CANTIDAD_CARGA': diff['cantidad_carga'],
            'CANTIDAD_BICE': diff['cantidad_bice'],
            'OBSERVACION': f"DIFERENCIA - Carga tiene {diff['cantidad_carga']} registros, BICE tiene {diff['cantidad_bice']} registros"
        })

    # 2. En Carga pero no en BICE
    for rut in carga_no_en_bice:
        reg_carga = df_carga[df_carga['RUT_NORM'] == rut].iloc[0]

        resultados.append({
            'RUT': rut,
            'ESTADO': 'CARGA_SIN_BICE',
            'TIPO': 'TINET',
            'NOMBRES_CARGA': reg_carga.get('Nombre', ''),
            'APELLIDOS_CARGA': f"{reg_carga.get('Apellido Paterno', '')} {reg_carga.get('Apellido Materno', '')}".strip(),
            'NOMBRE_BICE': '',
            'APELLIDO_BICE': '',
            'EMAIL_CARGA': reg_carga.get('Correo Tinet', ''),
            'EMAIL_BICE': '',
            'OBSERVACION': 'FALTA - RUT en Carga pero NO en BICE'
        })

    # 3. En BICE pero no en Carga
    for rut in bice_no_en_carga:
        reg_bice = df_bice[df_bice['RUT_NORM'] == rut].iloc[0]

        resultados.append({
            'RUT': rut,
            'ESTADO': 'BICE_SIN_CARGA',
            'TIPO': 'TINET',
            'NOMBRES_CARGA': '',
            'APELLIDOS_CARGA': '',
            'NOMBRE_BICE': reg_bice.get('Nombre', ''),
            'APELLIDO_BICE': reg_bice.get('Apellido', ''),
            'EMAIL_CARGA': '',
            'EMAIL_BICE': reg_bice.get('Email', '') or reg_bice.get('Correo', ''),
            'OBSERVACION': 'EXTRA - RUT en BICE pero NO en Carga'
        })

    # Crear DataFrame y guardar
    df_resultados = pd.DataFrame(resultados)

    orden_estados = {
        'COINCIDENCIA': 1,
        'DIFERENCIA_CANTIDAD': 2,
        'CARGA_SIN_BICE': 3,
        'BICE_SIN_CARGA': 4
    }

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    df_coincidencias, df_inconsistencias, archivos = separar_y_guardar_resultados(
        df_resultados, script_dir, timestamp, orden_estados
    )

    imprimir_resumen(df_coincidencias, df_inconsistencias, archivos)

    # Generar CSV especial para registros en CARGA que NO están en BICE (hay que agregarlos)
    df_carga_sin_bice = df_inconsistencias[df_inconsistencias['ESTADO'] == 'CARGA_SIN_BICE'].copy()
    if len(df_carga_sin_bice) > 0:
        # Preparar DataFrame con el formato requerido
        df_csv_carga = pd.DataFrame({
            'Nombre': df_carga_sin_bice['NOMBRES_CARGA'],
            'Apellido': df_carga_sin_bice['APELLIDOS_CARGA'],
            'Email': df_carga_sin_bice['EMAIL_CARGA'],
            'RUT': df_carga_sin_bice['RUT']
        })
        
        # Guardar en formato especial
        from utils.file_handlers import guardar_csv_formato_especial
        resultado_dir = os.path.join(script_dir, 'resultado')
        archivo_csv_carga = os.path.join(resultado_dir, f'carga_sin_bice_tinet_{timestamp}.csv')
        guardar_csv_formato_especial(df_csv_carga, archivo_csv_carga)
        print(f"   📄 Carga sin BICE (hay que agregar): {os.path.basename(archivo_csv_carga)}")

    # Generar CSV especial para registros en BICE que NO están en Carga
    df_bice_sin_carga = df_inconsistencias[df_inconsistencias['ESTADO'] == 'BICE_SIN_CARGA'].copy()
    if len(df_bice_sin_carga) > 0:
        # Preparar DataFrame con el formato requerido
        df_csv_especial = pd.DataFrame({
            'Nombre': df_bice_sin_carga['NOMBRE_BICE'],
            'Apellido': df_bice_sin_carga['APELLIDO_BICE'],
            'Email': df_bice_sin_carga['EMAIL_BICE'],
            'RUT': df_bice_sin_carga['RUT']
        })
        
        # Guardar en formato especial
        from utils.file_handlers import guardar_csv_formato_especial
        resultado_dir = os.path.join(script_dir, 'resultado')
        archivo_csv_especial = os.path.join(resultado_dir, f'bice_sin_carga_tinet_{timestamp}.csv')
        guardar_csv_formato_especial(df_csv_especial, archivo_csv_especial, solo_rut=True)
        print(f"   📄 BICE sin Carga (formato carga): {os.path.basename(archivo_csv_especial)}")

    if len(df_inconsistencias) > 0:
        print(f"\n🔍 Muestra de inconsistencias (primeros 10):")
        columnas_mostrar = ['RUT', 'ESTADO', 'NOMBRES_CARGA', 'NOMBRE_BICE', 'APELLIDO_BICE']
        print(df_inconsistencias.head(10)[columnas_mostrar].to_string(index=False))

    print("\n" + "="*80)
    print("✅ Proceso completado")
    print("="*80)


if __name__ == "__main__":
    comparar_tinet()
