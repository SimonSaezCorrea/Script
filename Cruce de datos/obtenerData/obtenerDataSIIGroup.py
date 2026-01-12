"""
Script para procesar datos de SII Group y generar archivos separados por estado activo.

Lee el archivo de Excel de SII Group y genera dos archivos:
- Activos: con formato Nombre, Apellido, Email, RUT
- Inactivos: con toda la data completa

El archivo de entrada debe estar en la carpeta 'data':
'Nómina PAWER Enero 2026 - SII Group Chile.xlsx'

Formato del Excel de SII Group:
Estado | Nombre | RUT | Correo | Teléfono | Dirección | Comuna
"""
import pandas as pd
import os
import sys

# Agregar la carpeta padre al path para poder importar utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.normalizers import normalizar_rut, normalizar_email
from utils.file_handlers import (
    encontrar_columnas,
    separar_por_activo,
    guardar_csv_formato_especial,
    guardar_excel_completo,
    leer_excel_flexible,
    buscar_archivo_en_data,
    asegurar_directorio_resultado
)


def separar_nombre_completo(nombre_completo):
    """
    Separa un nombre completo en nombre y apellidos.
    Asume formato: "Nombre Apellido1 Apellido2" o similar
    
    Args:
        nombre_completo: String con el nombre completo
    
    Returns:
        Tupla (nombre, apellidos)
    """
    if not nombre_completo or str(nombre_completo).strip() == '':
        return '', ''
    
    partes = str(nombre_completo).strip().split()
    
    if len(partes) == 0:
        return '', ''
    elif len(partes) == 1:
        return partes[0], ''
    elif len(partes) == 2:
        return partes[0], partes[1]
    else:
        # Primer parte es nombre, resto son apellidos
        nombre = partes[0]
        apellidos = ' '.join(partes[1:])
        return nombre, apellidos


def procesar_datos_siigroup():
    """
    Procesa el archivo de Excel de SII Group y genera archivos según el formato requerido.
    """
    # Rutas de archivos
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    
    # Buscar el archivo en la carpeta data
    archivo_entrada = buscar_archivo_en_data(base_dir, ['Nómina PAWER', 'SII Group'])
    
    if not archivo_entrada:
        # Intentar buscar directamente el nombre específico
        archivo_entrada = os.path.join(base_dir, 'data', 'Nómina PAWER Enero 2026 - SII Group Chile.xlsx')
        if not os.path.exists(archivo_entrada):
            print(f"Error: No se encontró el archivo de datos de SII Group en {os.path.join(base_dir, 'data')}")
            print("Buscando archivo que contenga 'Nómina PAWER' y 'SII Group'")
            return
    
    # Carpeta de salida
    resultado_dir = asegurar_directorio_resultado(base_dir)
    archivo_activos = os.path.join(resultado_dir, 'datos_siigroup_activos.csv')
    archivo_inactivos = os.path.join(resultado_dir, 'datos_siigroup_inactivos.xlsx')
    
    print(f"Leyendo archivo: {archivo_entrada}")
    
    try:
        # Leer el archivo Excel
        df = leer_excel_flexible(archivo_entrada)
        
        print(f"Archivo leído correctamente. {len(df)} registros encontrados.")
        print(f"Columnas encontradas: {list(df.columns)}")
        
        # Mapeo de columnas esperadas
        # Formato original: Estado | Nombre | RUT | Correo | Teléfono | Dirección | Comuna
        columnas_esperadas = {
            'estado': ['Estado', 'Activo'],
            'nombre': ['Nombre', 'Nombres'],
            'rut': ['RUT', 'Rut'],
            'email': ['Correo', 'Email', 'Correo electrónico'],
        }
        
        # Encontrar nombres de columnas reales
        columnas_reales = encontrar_columnas(df, columnas_esperadas)
        
        # Verificar que se encontraron todas las columnas necesarias
        columnas_faltantes = [k for k in ['nombre', 'rut', 'email'] 
                            if k not in columnas_reales]
        if columnas_faltantes:
            print(f"Advertencia: No se encontraron las siguientes columnas: {columnas_faltantes}")
            print("Se usarán valores vacíos para estas columnas.")
        
        # Separar datos por estado activo
        col_estado = columnas_reales.get('estado')
        df_activos, df_inactivos = separar_por_activo(df, col_estado)
        
        if col_estado:
            print(f"\nRegistros activos: {len(df_activos)}")
            print(f"Registros inactivos: {len(df_inactivos)}")
        else:
            print(f"\nAdvertencia: No se encontró la columna 'Estado'. Se procesarán todos los {len(df_activos)} registros como activos.")
        
        # ===== PROCESAR ACTIVOS (formato simplificado) =====
        df_activos_salida = pd.DataFrame()
        
        # Separar nombre completo en nombre y apellidos
        if 'nombre' in columnas_reales:
            nombres_apellidos = df_activos[columnas_reales['nombre']].fillna('').apply(separar_nombre_completo)
            df_activos_salida['Nombre'] = [n for n, a in nombres_apellidos]
            df_activos_salida['Apellido'] = [a for n, a in nombres_apellidos]
        else:
            df_activos_salida['Nombre'] = ''
            df_activos_salida['Apellido'] = ''
        
        # Email (normalizado a minúsculas)
        if 'email' in columnas_reales:
            df_activos_salida['Email'] = df_activos[columnas_reales['email']].fillna('').apply(normalizar_email)
        else:
            df_activos_salida['Email'] = ''
        
        # RUT (sin puntos ni guión)
        if 'rut' in columnas_reales:
            df_activos_salida['RUT'] = df_activos[columnas_reales['rut']].fillna('').apply(normalizar_rut)
        else:
            df_activos_salida['RUT'] = ''
        
        # Guardar archivo de activos en formato CSV personalizado
        guardar_csv_formato_especial(df_activos_salida, archivo_activos)
        
        print(f"\nArchivo de activos guardado en: {archivo_activos}")
        print(f"Registros activos procesados: {len(df_activos_salida)}")
        
        # Mostrar vista previa de activos
        if len(df_activos_salida) > 0:
            print("\nVista previa de activos (primeros 5 registros):")
            print(df_activos_salida.head().to_string(index=False))
        
        # ===== PROCESAR INACTIVOS (data completa) =====
        if len(df_inactivos) > 0:
            # Guardar archivo de inactivos con TODA la data
            guardar_excel_completo(df_inactivos, archivo_inactivos)
            
            print(f"\nArchivo de inactivos guardado en: {archivo_inactivos}")
            print(f"Registros inactivos procesados: {len(df_inactivos)}")
            
            # Mostrar vista previa de inactivos
            print("\nVista previa de inactivos (primeros 3 registros):")
            print(df_inactivos.head(3).to_string(index=False))
        else:
            print("\nNo hay registros inactivos para procesar.")
        
        print(f"\n✓ Proceso completado exitosamente!")
        
    except Exception as e:
        print(f"Error al procesar el archivo: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    procesar_datos_siigroup()
