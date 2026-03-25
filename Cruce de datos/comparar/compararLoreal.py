"""
Script para comparar datos entre archivo de carga L'Oréal y archivo BICE L'Oréal.

Compara RUTs y reporta inconsistencias.

Columnas del archivo de carga L'Oréal:
- A: Nombre
- B: email corporativo
- C: Rut

Archivos esperados en carpeta `data/Loreal`:
- [archivo con nombre Loreal].xlsx (CARGA)
- Loreal_users_[fecha].xlsx (BICE)
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
from utils.file_handlers import guardar_csv_formato_especial


def comparar_loreal():
    """
    Compara los RUTs entre el archivo de carga y el archivo BICE de L'Oréal.
    """
    # Rutas de archivos
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, 'data', 'Loreal')

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

        if 'Loreal_users' in filename or "L'Oreal_users" in filename or "Loreal_users" in filename:
            archivo_bice = os.path.join(data_dir, filename)
        elif filename.endswith('.xlsx'):
            archivo_carga = os.path.join(data_dir, filename)

    if not archivo_carga or not archivo_bice:
        print("❌ Error: No se encontraron todos los archivos necesarios")
        print(f"   Carga encontrado: {archivo_carga is not None}")
        print(f"   BICE encontrado: {archivo_bice is not None}")
        return

    print("="*80)
    print("📊 COMPARACIÓN CARGA vs BICE - L'ORÉAL")
    print("="*80)
    print(f"\nArchivo Carga: {os.path.basename(archivo_carga)}")
    print(f"Archivo BICE: {os.path.basename(archivo_bice)}")

    # Leer archivos
    print("\n🔄 Leyendo archivos...")

    # Leer Carga (Excel)
    try:
        df_carga = pd.read_excel(archivo_carga)
        print(f"  ✓ Archivo Carga leído correctamente ({len(df_carga)} registros)")
    except Exception as e:
        print(f"  ❌ Error al leer archivo de carga: {e}")
        return

    # Leer BICE (Excel)
    try:
        df_bice = pd.read_excel(archivo_bice)
        print(f"  ✓ Archivo BICE leído correctamente ({len(df_bice)} registros)")
    except Exception as e:
        print(f"  ❌ Error al leer archivo BICE: {e}")
        return

    # Verificar columnas del archivo de carga
    print("\n🔍 Columnas encontradas en Carga:")
    print(f"  {', '.join(df_carga.columns.tolist())}")

    # Detectar columnas de Nombre, Email y RUT en la carga
    col_nombre_carga = None
    col_email_carga = None
    col_rut_carga = None

    for col in df_carga.columns:
        col_lower = str(col).lower().strip()
        if col_lower == 'nombre':
            col_nombre_carga = col
        elif 'email' in col_lower or 'correo' in col_lower or 'mail' in col_lower:
            col_email_carga = col
        elif 'rut' in col_lower:
            col_rut_carga = col

    if not col_rut_carga:
        print("  ❌ No se encontró columna 'Rut' en el archivo de carga")
        return

    print(f"  ✓ Nombre: '{col_nombre_carga}'")
    print(f"  ✓ Email: '{col_email_carga}'")
    print(f"  ✓ RUT: '{col_rut_carga}'")

    # Renombrar columna RUT de carga para normalización
    df_carga = df_carga.rename(columns={col_rut_carga: 'RUT'})

    # Separar nombre completo en Apellido y Nombre según el formato:
    # "Apellido1 Apellido2 Nombre1 Nombre2" → las primeras ceil(n/2) palabras son apellido,
    # el resto son nombre. Ejemplos:
    #   4 palabras → 2 apellidos + 2 nombres
    #   3 palabras → 2 apellidos + 1 nombre
    #   2 palabras → 1 apellido  + 1 nombre
    import math

    def split_nombre_completo(nombre_completo):
        if not nombre_completo or pd.isna(nombre_completo):
            return '', ''
        partes = str(nombre_completo).strip().split()
        n = len(partes)
        n_apellido = math.ceil(n / 2)
        apellido = ' '.join(p.capitalize() for p in partes[:n_apellido])
        nombre = ' '.join(p.capitalize() for p in partes[n_apellido:])
        return nombre, apellido

    def extraer_nombre(nombre_completo):
        return split_nombre_completo(nombre_completo)[0]

    def extraer_apellido(nombre_completo):
        return split_nombre_completo(nombre_completo)[1]

    if col_nombre_carga:
        df_carga['_Nombre'] = df_carga[col_nombre_carga].apply(extraer_nombre)
        df_carga['_Apellido'] = df_carga[col_nombre_carga].apply(extraer_apellido)
    else:
        df_carga['_Nombre'] = ''
        df_carga['_Apellido'] = ''

    # Email en lowercase
    if col_email_carga:
        df_carga[col_email_carga] = df_carga[col_email_carga].apply(
            lambda x: str(x).strip().lower() if pd.notna(x) and str(x).strip() != '' else ''
        )

    print(f"\n📈 Registros totales:")
    print(f"  - Carga: {len(df_carga)}")
    print(f"  - BICE (total): {len(df_bice)}")

    # Filtrar solo registros activos en archivo BICE
    if 'Estado' in df_bice.columns:
        df_bice = filtrar_activos(df_bice, 'Estado')
        print(f"  - BICE (activos): {len(df_bice)}")

    # Procesar RUTs
    print("\n🔧 Procesando RUTs...")

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

    # Crear DataFrames de resultados
    resultados = []
    ruts_con_diferencia_cantidad = set([d['rut'] for d in diferencias_cantidad])

    # 1. Coincidencias (con cantidad correcta)
    for rut in coincidencias:
        if rut in ruts_con_diferencia_cantidad:
            continue

        reg_carga = df_carga[df_carga['RUT_NORM'] == rut].iloc[0]
        reg_bice = df_bice[df_bice['RUT_NORM'] == rut].iloc[0]

        resultados.append({
            'RUT': rut,
            'ESTADO': 'COINCIDENCIA',
            'TIPO': 'LOREAL',
            'NOMBRE_CARGA': reg_carga.get('_Nombre', ''),
            'APELLIDO_CARGA': reg_carga.get('_Apellido', ''),
            'NOMBRE_BICE': reg_bice.get('Nombre', ''),
            'EMAIL_CARGA': reg_carga.get(col_email_carga, '') if col_email_carga else '',
            'EMAIL_BICE': reg_bice.get('Email', ''),
            'CANTIDAD_CARGA': len(df_carga[df_carga['RUT_NORM'] == rut]),
            'CANTIDAD_BICE': len(df_bice[df_bice['RUT_NORM'] == rut]),
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
            'TIPO': 'LOREAL',
            'NOMBRE_CARGA': reg_carga.get('_Nombre', ''),
            'APELLIDO_CARGA': reg_carga.get('_Apellido', ''),
            'NOMBRE_BICE': reg_bice.get('Nombre', ''),
            'EMAIL_CARGA': reg_carga.get(col_email_carga, '') if col_email_carga else '',
            'EMAIL_BICE': reg_bice.get('Email', ''),
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
            'TIPO': 'LOREAL',
            'NOMBRE_CARGA': reg_carga.get('_Nombre', ''),
            'APELLIDO_CARGA': reg_carga.get('_Apellido', ''),
            'NOMBRE_BICE': '',
            'EMAIL_CARGA': reg_carga.get(col_email_carga, '') if col_email_carga else '',
            'EMAIL_BICE': '',
            'CANTIDAD_CARGA': len(df_carga[df_carga['RUT_NORM'] == rut]),
            'CANTIDAD_BICE': 0,
            'OBSERVACION': 'FALTA - RUT en Carga pero NO en BICE'
        })

    # 3. En BICE pero no en Carga
    for rut in bice_no_en_carga:
        reg_bice = df_bice[df_bice['RUT_NORM'] == rut].iloc[0]

        resultados.append({
            'RUT': rut,
            'ESTADO': 'BICE_SIN_CARGA',
            'TIPO': 'LOREAL',
            'NOMBRE_CARGA': '',
            'APELLIDO_CARGA': '',
            'NOMBRE_BICE': reg_bice.get('Nombre', ''),
            'EMAIL_CARGA': '',
            'EMAIL_BICE': reg_bice.get('Email', ''),
            'CANTIDAD_CARGA': 0,
            'CANTIDAD_BICE': len(df_bice[df_bice['RUT_NORM'] == rut]),
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

    # Crear carpeta de resultado
    resultado_dir = os.path.join(script_dir, 'resultado')
    os.makedirs(resultado_dir, exist_ok=True)

    # Generar CSV especial para registros en CARGA que NO están en BICE (hay que agregarlos)
    df_carga_sin_bice = df_inconsistencias[df_inconsistencias['ESTADO'] == 'CARGA_SIN_BICE'].copy()
    if len(df_carga_sin_bice) > 0:
        df_csv_carga = pd.DataFrame({
            'Nombre': df_carga_sin_bice['NOMBRE_CARGA'],
            'Apellido': df_carga_sin_bice['APELLIDO_CARGA'],
            'Email': df_carga_sin_bice['EMAIL_CARGA'],
            'RUT': df_carga_sin_bice['RUT']
        })

        archivo_csv_carga = os.path.join(resultado_dir, f'carga_sin_bice_loreal_{timestamp}.csv')
        guardar_csv_formato_especial(df_csv_carga, archivo_csv_carga)
        print(f"   📄 Carga sin BICE (hay que agregar): {os.path.basename(archivo_csv_carga)}")

    # Generar CSV especial para registros en BICE que NO están en Carga
    df_bice_sin_carga = df_inconsistencias[df_inconsistencias['ESTADO'] == 'BICE_SIN_CARGA'].copy()
    if len(df_bice_sin_carga) > 0:
        df_csv_especial = pd.DataFrame({
            'Nombre': df_bice_sin_carga['NOMBRE_BICE'],
            'Apellido': '',
            'Email': df_bice_sin_carga['EMAIL_BICE'],
            'RUT': df_bice_sin_carga['RUT']
        })

        archivo_csv_especial = os.path.join(resultado_dir, f'bice_sin_carga_loreal_{timestamp}.csv')
        guardar_csv_formato_especial(df_csv_especial, archivo_csv_especial, solo_rut=True)
        print(f"   📄 BICE sin Carga (formato carga): {os.path.basename(archivo_csv_especial)}")

    # Mostrar muestras
    if len(df_inconsistencias) > 0:
        print(f"\n🔍 Muestra de inconsistencias (primeros 10):")
        columnas_mostrar = ['RUT', 'ESTADO', 'NOMBRE_CARGA', 'NOMBRE_BICE']
        print(df_inconsistencias.head(10)[columnas_mostrar].to_string(index=False))

    print("\n" + "="*80)
    print("✅ Proceso completado")
    print("="*80)


if __name__ == "__main__":
    comparar_loreal()
