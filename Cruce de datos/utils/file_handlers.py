"""
Funciones de utilidad para manejo de archivos y procesamiento de datos
"""
import pandas as pd
import os


def encontrar_columnas(df, columnas_esperadas):
    """
    Encuentra las columnas reales en un DataFrame basándose en nombres posibles.
    
    Args:
        df: DataFrame de pandas
        columnas_esperadas: Diccionario con formato {key: [lista de nombres posibles]}
    
    Returns:
        Diccionario con {key: nombre_columna_real}
    """
    columnas_reales = {}
    for key, posibles_nombres in columnas_esperadas.items():
        for col in df.columns:
            if any(nombre.lower() in col.lower() for nombre in posibles_nombres):
                columnas_reales[key] = col
                break
    return columnas_reales


def separar_por_activo(df, columna_activo=None):
    """
    Separa un DataFrame en activos e inactivos basándose en una columna booleana.
    
    Args:
        df: DataFrame de pandas
        columna_activo: Nombre de la columna que indica si está activo (opcional)
    
    Returns:
        Tupla (df_activos, df_inactivos)
    """
    if columna_activo and columna_activo in df.columns:
        # Convertir a booleano, considerando diferentes formatos
        df[columna_activo] = df[columna_activo].apply(
            lambda x: str(x).upper() in ['TRUE', 'VERDADERO', 'SI', 'SÍ', 'YES', '1', 'ACTIVO']
        )
        
        df_activos = df[df[columna_activo] == True].copy()
        df_inactivos = df[df[columna_activo] == False].copy()
    else:
        # Si no hay columna activo, todos son activos
        df_activos = df.copy()
        df_inactivos = pd.DataFrame()
    
    return df_activos, df_inactivos


def guardar_csv_formato_especial(df, archivo_salida, columnas=['Nombre', 'Apellido', 'Email', 'RUT'], solo_rut=False):
    """
    Guarda un DataFrame en formato CSV especial: "campo1,campo2,campo3,campo4",
    O en formato simplificado solo con RUTs: "rut1",
    
    Args:
        df: DataFrame de pandas con las columnas a guardar
        archivo_salida: Ruta del archivo de salida
        columnas: Lista de nombres de columnas en el orden deseado
        solo_rut: Si es True, solo guarda la columna RUT en formato simple
    
    Returns:
        None
    """
    with open(archivo_salida, 'w', encoding='utf-8-sig') as f:
        if solo_rut:
            # Formato simplificado: solo RUTs
            for _, row in df.iterrows():
                f.write(f'"{row["RUT"]}",\n')
        else:
            # Formato completo con encabezado
            encabezado = ','.join(columnas)
            f.write(f'"{encabezado}"\n')
            
            # Escribir cada fila
            for _, row in df.iterrows():
                valores = [str(row[col]) for col in columnas]
                linea = ','.join(valores)
                f.write(f'"{linea}",\n')


def guardar_excel_completo(df, archivo_salida):
    """
    Guarda un DataFrame completo en formato Excel.
    
    Args:
        df: DataFrame de pandas
        archivo_salida: Ruta del archivo de salida
    
    Returns:
        None
    """
    df.to_excel(archivo_salida, index=False, engine='openpyxl')


def crear_dataframe_procesado(df, columnas_reales, normalizar_rut_func, normalizar_email_func, combinar_apellidos_func):
    """
    Crea un DataFrame procesado con formato estándar: Nombre, Apellido, Email, RUT
    
    Args:
        df: DataFrame original
        columnas_reales: Diccionario con mapeo de columnas
        normalizar_rut_func: Función para normalizar RUT
        normalizar_email_func: Función para normalizar email
        combinar_apellidos_func: Función para combinar apellidos
    
    Returns:
        DataFrame procesado
    """
    df_salida = pd.DataFrame()
    
    # Nombre
    if 'nombre' in columnas_reales:
        df_salida['Nombre'] = df[columnas_reales['nombre']].fillna('')
    else:
        df_salida['Nombre'] = ''
    
    # Apellido (combinar paterno y materno)
    apellido_paterno = df[columnas_reales['apellido_paterno']].fillna('') if 'apellido_paterno' in columnas_reales else pd.Series([''] * len(df))
    apellido_materno = df[columnas_reales['apellido_materno']].fillna('') if 'apellido_materno' in columnas_reales else pd.Series([''] * len(df))
    
    df_salida['Apellido'] = [combinar_apellidos_func(p, m) for p, m in zip(apellido_paterno, apellido_materno)]
    
    # Email (normalizado a minúsculas)
    if 'email' in columnas_reales:
        df_salida['Email'] = df[columnas_reales['email']].fillna('').apply(normalizar_email_func)
    else:
        df_salida['Email'] = ''
    
    # RUT (sin puntos ni guión)
    if 'rut' in columnas_reales:
        df_salida['RUT'] = df[columnas_reales['rut']].fillna('').apply(normalizar_rut_func)
    else:
        df_salida['RUT'] = ''
    
    return df_salida


def leer_excel_flexible(archivo_entrada):
    """
    Lee un archivo Excel con diferentes extensiones posibles.
    
    Args:
        archivo_entrada: Ruta del archivo (con o sin extensión)
    
    Returns:
        DataFrame de pandas
    """
    if archivo_entrada.endswith('.xlsx') or archivo_entrada.endswith('.xls'):
        return pd.read_excel(archivo_entrada)
    else:
        # Intentar con xlsx primero
        try:
            return pd.read_excel(archivo_entrada + '.xlsx')
        except:
            return pd.read_excel(archivo_entrada + '.xls')


def buscar_archivo_en_data(base_dir, patron_busqueda):
    """
    Busca un archivo en la carpeta data que coincida con un patrón.
    
    Args:
        base_dir: Directorio base del proyecto
        patron_busqueda: Lista de strings que deben estar en el nombre del archivo
    
    Returns:
        Ruta completa del archivo encontrado o None
    """
    # Buscar en posibles ubicaciones de la carpeta `data`.
    posibles_dirs = [
        os.path.join(base_dir, 'data'),
        os.path.join(base_dir, 'obtenerData', 'data')
    ]

    for data_dir in posibles_dirs:
        if not os.path.exists(data_dir):
            continue

        for filename in os.listdir(data_dir):
            nombre_lower = filename.lower()
            if all(patron.lower() in nombre_lower for patron in patron_busqueda):
                return os.path.join(data_dir, filename)

    return None


def asegurar_directorio_resultado(base_dir):
    """
    Asegura que existe el directorio de resultados.
    
    Args:
        base_dir: Directorio base del proyecto
    
    Returns:
        Ruta del directorio de resultados
    """
    # Guardar resultados dentro de la carpeta `obtenerData/resultado`
    resultado_dir = os.path.join(base_dir, 'obtenerData', 'resultado')
    os.makedirs(resultado_dir, exist_ok=True)
    return resultado_dir
