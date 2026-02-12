"""
Funciones comunes para comparar archivos de carga vs BICE
"""
import pandas as pd
import os


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


def filtrar_activos(df, columna_estado='Estado'):
    """
    Filtra un DataFrame para obtener solo registros activos.
    
    Args:
        df: DataFrame de pandas
        columna_estado: Nombre de la columna de estado
    
    Returns:
        DataFrame filtrado con solo registros activos
    """
    if columna_estado in df.columns:
        # Convertir a string para manejar booleanos
        df[columna_estado] = df[columna_estado].astype(str).str.upper()
        return df[df[columna_estado].isin(['VERDADERO', 'TRUE', 'ACTIVO', '1'])].copy()
    return df.copy()


def normalizar_ruts_dataframe(df, columna_rut='RUT'):
    """
    Normaliza los RUTs en un DataFrame y elimina los vacíos.
    
    Args:
        df: DataFrame de pandas
        columna_rut: Nombre de la columna con el RUT
    
    Returns:
        DataFrame con columna RUT_NORM agregada y RUTs vacíos eliminados
    """
    # Verificar si la columna existe
    if columna_rut not in df.columns:
        # Buscar columna similar (case insensitive)
        for col in df.columns:
            if col.lower() == columna_rut.lower():
                columna_rut = col
                break
    
    df['RUT_NORM'] = df[columna_rut].apply(normalizar_rut_comparacion)
    return df[df['RUT_NORM'] != ''].copy()


def crear_resultados_comparacion(rut, estado, tipo, reg_carga, reg_bice, columnas_carga, columnas_bice, observacion):
    """
    Crea un registro de resultado de comparación.
    
    Args:
        rut: RUT normalizado
        estado: Estado de la comparación
        tipo: Tipo de registro (OMG, PYME, etc.)
        reg_carga: Serie de pandas con datos de carga
        reg_bice: Serie de pandas con datos de BICE
        columnas_carga: Dict con nombres de columnas de carga
        columnas_bice: Dict con nombres de columnas de BICE
        observacion: Observación sobre el registro
    
    Returns:
        Diccionario con el resultado
    """
    resultado = {
        'RUT': rut,
        'ESTADO': estado,
        'TIPO': tipo,
        'OBSERVACION': observacion
    }
    
    # Agregar datos de carga si existen
    if reg_carga is not None:
        for key, col_name in columnas_carga.items():
            resultado[key] = reg_carga.get(col_name, '')
    else:
        for key in columnas_carga.keys():
            resultado[key] = ''
    
    # Agregar datos de BICE si existen
    if reg_bice is not None:
        for key, col_name in columnas_bice.items():
            resultado[key] = reg_bice.get(col_name, '')
    else:
        for key in columnas_bice.keys():
            resultado[key] = ''
    
    return resultado


def separar_y_guardar_resultados(df_resultados, script_dir, timestamp, orden_estados, prefijo=''):
    """
    Separa resultados en coincidencias e inconsistencias y los guarda.
    
    Args:
        df_resultados: DataFrame con todos los resultados
        script_dir: Directorio del script
        timestamp: Timestamp para los archivos
        orden_estados: Diccionario con orden de estados para sorting
        prefijo: Prefijo opcional para los nombres de archivo (ej: 'cencosud_', 'mercer_')
    
    Returns:
        Tuple (df_coincidencias, df_inconsistencias, archivos guardados)
    """
    # Ordenar por estado y RUT
    df_resultados['ORDEN'] = df_resultados['ESTADO'].map(orden_estados)
    df_resultados = df_resultados.sort_values(['ORDEN', 'RUT']).drop('ORDEN', axis=1)
    
    # Separar en dos DataFrames
    df_coincidencias = df_resultados[df_resultados['ESTADO'].str.contains('COINCIDENCIA')].copy()
    df_inconsistencias = df_resultados[~df_resultados['ESTADO'].str.contains('COINCIDENCIA')].copy()
    
    # Guardar resultados
    resultado_dir = os.path.join(script_dir, 'resultado')
    os.makedirs(resultado_dir, exist_ok=True)
    
    archivo_coincidencias = os.path.join(resultado_dir, f'{prefijo}comparacion_coincidencias_{timestamp}.xlsx')
    df_coincidencias.to_excel(archivo_coincidencias, index=False)
    
    archivo_inconsistencias = os.path.join(resultado_dir, f'{prefijo}comparacion_inconsistencias_{timestamp}.xlsx')
    df_inconsistencias.to_excel(archivo_inconsistencias, index=False)
    
    return df_coincidencias, df_inconsistencias, (archivo_coincidencias, archivo_inconsistencias)


def imprimir_resumen(df_coincidencias, df_inconsistencias, archivos):
    """
    Imprime el resumen de resultados.
    
    Args:
        df_coincidencias: DataFrame con coincidencias
        df_inconsistencias: DataFrame con inconsistencias
        archivos: Tuple con rutas de archivos guardados
    """
    archivo_coincidencias, archivo_inconsistencias = archivos
    
    print("\n💾 Resultados guardados en:")
    print(f"   📗 Coincidencias: {os.path.basename(archivo_coincidencias)}")
    print(f"   📕 Inconsistencias: {os.path.basename(archivo_inconsistencias)}")
    
    print("\n📋 Resumen por estado:")
    print(f"   ✅ COINCIDENCIAS: {len(df_coincidencias)}")
    if len(df_coincidencias) > 0:
        for estado, cantidad in df_coincidencias['ESTADO'].value_counts().items():
            print(f"      - {estado}: {cantidad}")
    
    print(f"   ⚠️  INCONSISTENCIAS: {len(df_inconsistencias)}")
    if len(df_inconsistencias) > 0:
        for estado, cantidad in df_inconsistencias['ESTADO'].value_counts().items():
            print(f"      - {estado}: {cantidad}")
