"""
Script para procesar datos de Sonda y generar archivos separados por estado activo.

Lee el archivo de Excel de Sonda y genera dos archivos:
- Activos: con formato Nombre, Apellido, Email, RUT
- Inactivos: con toda la data completa

El archivo de entrada debe estar en la carpeta 'data':
'Nomina Beneficio Seg Mascotas Pawer Dic 25- Sonda.xlsx'

Formato del Excel de Sonda:
Rut | Nombres | Primer apellido | Segundo apellido | Correo electrónico | Fecha contrato vigente
"""
import pandas as pd
import os
import sys

# Agregar la carpeta padre al path para poder importar utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.normalizers import normalizar_rut, normalizar_email, combinar_apellidos
from utils.file_handlers import (
    encontrar_columnas,
    separar_por_activo,
    guardar_csv_formato_especial,
    guardar_excel_completo,
    crear_dataframe_procesado,
    leer_excel_flexible,
    buscar_archivo_en_data,
    asegurar_directorio_resultado
)


def procesar_datos_sonda():
    """
    Procesa el archivo de Excel de Sonda y genera archivos según el formato requerido.
    """
    # Rutas de archivos
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    
    # Buscar el archivo en la carpeta data
    archivo_entrada = buscar_archivo_en_data(base_dir, ['Nomina Beneficio', 'Sonda'])
    
    if not archivo_entrada:
        # Intentar buscar directamente el nombre específico
        archivo_entrada = os.path.join(base_dir, 'data', 'Nomina Beneficio Seg Mascotas Pawer Dic 25- Sonda.xlsx')
        if not os.path.exists(archivo_entrada):
            print(f"Error: No se encontró el archivo de datos de Sonda en {os.path.join(base_dir, 'data')}")
            print("Buscando archivo que contenga 'Nomina Beneficio' y 'Sonda'")
            return
    
    # Carpeta de salida
    resultado_dir = asegurar_directorio_resultado(base_dir)
    archivo_activos = os.path.join(resultado_dir, 'datos_sonda_activos.csv')
    archivo_inactivos = os.path.join(resultado_dir, 'datos_sonda_inactivos.xlsx')
    
    print(f"Leyendo archivo: {archivo_entrada}")
    
    try:
        # Leer el archivo Excel
        df = leer_excel_flexible(archivo_entrada)
        
        print(f"Archivo leído correctamente. {len(df)} registros encontrados.")
        print(f"Columnas encontradas: {list(df.columns)}")
        
        # Mapeo de columnas esperadas
        # Formato original: Rut | Nombres | Primer apellido | Segundo apellido | Correo electrónico | Fecha contrato vigente
        columnas_esperadas = {
            'rut': ['Rut', 'RUT'],
            'nombre': ['Nombres', 'Nombre'],
            'apellido_paterno': ['Primer apellido', 'Apellido Paterno'],
            'apellido_materno': ['Segundo apellido', 'Apellido Materno'],
            'email': ['Correo electrónico', 'Correo', 'Email'],
            'activo': ['Activo', 'Estado']
        }
        
        # Encontrar nombres de columnas reales
        columnas_reales = encontrar_columnas(df, columnas_esperadas)
        
        # Verificar que se encontraron todas las columnas necesarias
        columnas_faltantes = [k for k in ['rut', 'nombre', 'apellido_paterno', 'apellido_materno', 'email'] 
                            if k not in columnas_reales]
        if columnas_faltantes:
            print(f"Advertencia: No se encontraron las siguientes columnas: {columnas_faltantes}")
            print("Se usarán valores vacíos para estas columnas.")
        
        # Separar datos por estado activo
        col_activo = columnas_reales.get('activo')
        df_activos, df_inactivos = separar_por_activo(df, col_activo)
        
        if col_activo:
            print(f"\nRegistros activos: {len(df_activos)}")
            print(f"Registros inactivos: {len(df_inactivos)}")
        else:
            print(f"\nAdvertencia: No se encontró la columna 'Activo'. Se procesarán todos los {len(df_activos)} registros como activos.")
        
        # ===== PROCESAR ACTIVOS (formato simplificado) =====
        df_activos_salida = crear_dataframe_procesado(
            df_activos,
            columnas_reales,
            normalizar_rut,
            normalizar_email,
            combinar_apellidos
        )
        
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
    procesar_datos_sonda()
