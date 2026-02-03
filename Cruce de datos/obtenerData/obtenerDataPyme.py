"""
Script para procesar datos PAWER y separar por empresa (OMG vs PYME).

Lee el archivo CSV de PAWER y genera dos archivos:
- OMG: empresas de Omnicom Media Group (formato Nombre, Apellido, Email, RUT)
- PYME: todas las demás empresas (formato Nombre, Apellido, Email, RUT)

Empresas OMG:
- DDB CHILE SPA
- INFLUENCE & RESEARCH S.A.
- MEDIA INTERACTIVE S A
- OMD CHILE SPA
- OMNICOM MEDIA GROUP CHILE S.A.
- PHD CHILE S.A.

Formato del CSV:
POLIZA | NOMBRE_CONTRATANTE | RUT_ASEGURADO | DV_ASEGURADO | PATERNO | MATERNO | NOMBRE CARGA | SEXO | FECHA_NACIMIENTO | CORREO | RUT CONT | DV CONT
"""
import pandas as pd
import os
import sys

# Agregar la carpeta padre al path para poder importar utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.normalizers import normalizar_email, combinar_apellidos, combinar_rut_dv, normalizar_nombre
from utils.file_handlers import (
    encontrar_columnas,
    separar_por_activo,
    guardar_csv_formato_especial,
    guardar_excel_completo,
    buscar_archivo_en_data,
    asegurar_directorio_resultado
)


def procesar_datos_pawer():
    """
    Procesa el archivo CSV de Pyme y genera archivos según el formato requerido.
    """
    # Rutas de archivos
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    
    # Buscar el archivo en la carpeta data del script (obtenerData/data)
    archivo_entrada = buscar_archivo_en_data(script_dir, ['PAWER'])
    
    if not archivo_entrada:
        # Intentar buscar directamente el nombre específico en el directorio del script
        archivo_entrada = os.path.join(script_dir, 'data', '20260127_PAWER Asistencia de Mascotas_FULL_Pawer_asist.csv')
        if not os.path.exists(archivo_entrada):
            # También intentar en el directorio base
            archivo_entrada = os.path.join(base_dir, 'data', '20260127_PAWER Asistencia de Mascotas_FULL_Pawer_asist.csv')
            if not os.path.exists(archivo_entrada):
                print(f"Error: No se encontró el archivo de datos de Pyme en:")
                print(f"  - {os.path.join(script_dir, 'data')}")
                print(f"  - {os.path.join(base_dir, 'data')}")
                print("Buscando archivo que contenga 'PAWER'")
                return
    
    # Carpeta de salida
    resultado_dir = asegurar_directorio_resultado(base_dir)
    archivo_omg = os.path.join(resultado_dir, 'datos_omg.csv')
    archivo_pyme = os.path.join(resultado_dir, 'datos_pyme.csv')
    
    print(f"Leyendo archivo: {archivo_entrada}")
    
    try:
        # Leer el archivo CSV con diferentes encodings y delimitadores
        encodings = ['utf-8-sig', 'latin-1', 'iso-8859-1', 'cp1252']
        delimitadores = [',', ';', '\t', '|']
        df = None
        
        for encoding in encodings:
            for delim in delimitadores:
                try:
                    df = pd.read_csv(
                        archivo_entrada, 
                        encoding=encoding,
                        delimiter=delim,
                        on_bad_lines='skip',  # Saltar líneas problemáticas
                        engine='python'  # Motor más flexible
                    )
                    # Verificar que tenga columnas razonables
                    if len(df.columns) > 5:
                        print(f"Archivo leído correctamente con encoding '{encoding}' y delimitador '{delim}'.")
                        break
                except Exception:
                    continue
            if df is not None and len(df.columns) > 5:
                break
        
        if df is None or len(df.columns) <= 5:
            print("Error: No se pudo leer el archivo con ninguna combinación de encoding/delimitador.")
            print("Intentando lectura automática...")
            try:
                df = pd.read_csv(archivo_entrada, encoding='latin-1', on_bad_lines='skip', engine='python')
            except Exception as e:
                print(f"Error final: {e}")
                return
        
        print(f"{len(df)} registros encontrados.")
        print(f"Columnas encontradas: {list(df.columns)}")
        
        # Mapeo de columnas esperadas
        # Formato original: POLIZA | NOMBRE_CONTRATANTE | RUT_ASEGURADO | DV_ASEGURADO | PATERNO | MATERNO | NOMBRE CARGA | SEXO | FECHA_NACIMIENTO | CORREO | RUT CONT | DV CONT
        # IMPORTANTE: Usar NOMBRE CARGA, NO NOMBRE_CONTRATANTE
        columnas_esperadas = {
            'nombre': ['NOMBRE CARGA', 'NOMBRE_CARGA'],
            'apellido_paterno': ['PATERNO'],
            'apellido_materno': ['MATERNO'],
            'rut': ['RUT_ASEGURADO', 'RUT ASEGURADO'],
            'dv': ['DV_ASEGURADO', 'DV ASEGURADO'],
            'email': ['CORREO', 'Email', 'Correo electrónico'],
            'empresa': ['NOMBRE_CONTRATANTE', 'NOMBRE CONTRATANTE']
        }
        
        # Encontrar nombres de columnas reales con coincidencia exacta para evitar confusiones
        columnas_reales = {}
        for key, posibles_nombres in columnas_esperadas.items():
            for col in df.columns:
                # Primero intentar coincidencia exacta (case insensitive)
                if col.strip().upper() in [nombre.upper() for nombre in posibles_nombres]:
                    columnas_reales[key] = col
                    break
            # Si no se encontró con coincidencia exacta, intentar con 'in'
            if key not in columnas_reales:
                for col in df.columns:
                    if any(nombre.lower() in col.lower() for nombre in posibles_nombres):
                        columnas_reales[key] = col
                        break
        
        print(f"\nColumnas mapeadas:")
        for key, col in columnas_reales.items():
            print(f"  {key}: '{col}'")
        
        # Verificar que se encontraron todas las columnas necesarias
        columnas_faltantes = [k for k in ['nombre', 'apellido_paterno', 'apellido_materno', 'rut', 'dv', 'email', 'empresa'] 
                            if k not in columnas_reales]
        if columnas_faltantes:
            print(f"Advertencia: No se encontraron las siguientes columnas: {columnas_faltantes}")
            print("Se usarán valores vacíos para estas columnas.")
        
        # Definir empresas OMG
        empresas_omg = {
            'DDB CHILE SPA',
            'INFLUENCE & RESEARCH S.A.',
            'MEDIA INTERACTIVE S A',
            'OMD CHILE SPA',
            'OMNICOM MEDIA GROUP CHILE S.A.',
            'PHD CHILE S.A.'
        }
        
        # Separar datos por empresa (OMG vs PYME)
        col_empresa = columnas_reales.get('empresa')
        if col_empresa:
            # Normalizar nombres de empresas para comparación
            df['empresa_normalizada'] = df[col_empresa].fillna('').str.strip().str.upper()
            empresas_omg_upper = {empresa.upper() for empresa in empresas_omg}
            
            df_omg = df[df['empresa_normalizada'].isin(empresas_omg_upper)].copy()
            df_pyme = df[~df['empresa_normalizada'].isin(empresas_omg_upper)].copy()
            
            print(f"\nRegistros OMG: {len(df_omg)}")
            print(f"Registros PYME: {len(df_pyme)}")
            
            # Mostrar distribución por empresa OMG
            if len(df_omg) > 0:
                print("\nDistribución OMG por empresa:")
                distribucion_omg = df_omg[col_empresa].value_counts()
                for empresa, count in distribucion_omg.items():
                    print(f"  - {empresa}: {count} registros")
        else:
            print(f"\nError: No se encontró la columna de empresa. No se puede separar OMG de PYME.")
            return
        
        # ===== PROCESAR OMG =====
        if len(df_omg) > 0:
            df_omg_salida = procesar_grupo_datos(df_omg, columnas_reales, "OMG")
            guardar_csv_formato_especial(df_omg_salida, archivo_omg)
            print(f"\nArchivo OMG guardado en: {archivo_omg}")
            print(f"Registros OMG procesados: {len(df_omg_salida)}")
            
            # Mostrar vista previa
            if len(df_omg_salida) > 0:
                print("\nVista previa OMG (primeros 5 registros):")
                print(df_omg_salida.head().to_string(index=False))
        else:
            print("\nNo hay registros OMG para procesar.")
        
        # ===== PROCESAR PYME =====
        if len(df_pyme) > 0:
            df_pyme_salida = procesar_grupo_datos(df_pyme, columnas_reales, "PYME")
            guardar_csv_formato_especial(df_pyme_salida, archivo_pyme)
            print(f"\nArchivo PYME guardado en: {archivo_pyme}")
            print(f"Registros PYME procesados: {len(df_pyme_salida)}")
            
            # Mostrar vista previa
            if len(df_pyme_salida) > 0:
                print("\nVista previa PYME (primeros 5 registros):")
                print(df_pyme_salida.head().to_string(index=False))
        else:
            print("\nNo hay registros PYME para procesar.")
        
        # ===== ANÁLISIS DE DUPLICADOS COMBINADO =====
        if len(df_omg) > 0 and len(df_pyme) > 0:
            df_total_salida = pd.concat([df_omg_salida, df_pyme_salida], ignore_index=True)
        elif len(df_omg) > 0:
            df_total_salida = df_omg_salida
        elif len(df_pyme) > 0:
            df_total_salida = df_pyme_salida
        else:
            print("\nNo hay datos para procesar.")
            return
            
        analizar_duplicados(df_total_salida)

        print(f"\n✓ Proceso completado exitosamente!")
        print(f"\n📁 Archivos generados:")
        if len(df_omg) > 0:
            print(f"  - OMG: {archivo_omg} ({len(df_omg_salida)} registros)")
        if len(df_pyme) > 0:
            print(f"  - PYME: {archivo_pyme} ({len(df_pyme_salida)} registros)")
        
        print(f"\n✓ Proceso completado exitosamente!")
        print(f"\n📁 Archivos generados:")
        if len(df_omg) > 0:
            print(f"  - OMG: {archivo_omg} ({len(df_omg_salida)} registros)")
        if len(df_pyme) > 0:
            print(f"  - PYME: {archivo_pyme} ({len(df_pyme_salida)} registros)")
        
    except Exception as e:
        print(f"Error al procesar el archivo: {str(e)}")
        import traceback
        traceback.print_exc()


def procesar_grupo_datos(df_grupo, columnas_reales, tipo_grupo):
    """
    Procesa un grupo de datos (OMG o PYME) y retorna el DataFrame con formato estándar.
    """
    df_salida = pd.DataFrame()
    
    # Nombre (normalizado con primera letra en mayúscula)
    if 'nombre' in columnas_reales:
        df_salida['Nombre'] = df_grupo[columnas_reales['nombre']].fillna('').apply(normalizar_nombre)
    else:
        df_salida['Nombre'] = ''
    
    # Apellido (combinar paterno y materno, normalizado)
    apellido_paterno = df_grupo[columnas_reales['apellido_paterno']].fillna('').apply(normalizar_nombre) if 'apellido_paterno' in columnas_reales else pd.Series([''] * len(df_grupo))
    apellido_materno = df_grupo[columnas_reales['apellido_materno']].fillna('').apply(normalizar_nombre) if 'apellido_materno' in columnas_reales else pd.Series([''] * len(df_grupo))
    
    df_salida['Apellido'] = [combinar_apellidos(p, m) for p, m in zip(apellido_paterno, apellido_materno)]
    
    # Email (normalizado a minúsculas)
    if 'email' in columnas_reales:
        df_salida['Email'] = df_grupo[columnas_reales['email']].fillna('').apply(normalizar_email)
    else:
        df_salida['Email'] = ''
    
    # Asignar correos ficticios a los registros sin email
    correo_ficticio_counter = 1
    for idx in df_salida.index:
        if df_salida.loc[idx, 'Email'] == '' or df_salida.loc[idx, 'Email'].strip() == '':
            df_salida.loc[idx, 'Email'] = f'correo-ficticio-{tipo_grupo.lower()}-{correo_ficticio_counter}@sincorreo.com'
            correo_ficticio_counter += 1
    
    # RUT (combinar RUT y DV sin puntos ni guión)
    if 'rut' in columnas_reales and 'dv' in columnas_reales:
        rut_series = df_grupo[columnas_reales['rut']].fillna('')
        dv_series = df_grupo[columnas_reales['dv']].fillna('')
        df_salida['RUT'] = [combinar_rut_dv(r, d) for r, d in zip(rut_series, dv_series)]
    elif 'rut' in columnas_reales:
        df_salida['RUT'] = df_grupo[columnas_reales['rut']].fillna('').astype(str)
    else:
        df_salida['RUT'] = ''
    
    return df_salida


def analizar_duplicados(df_salida):
    """
    Analiza y reporta duplicados en el DataFrame procesado.
    """
    print("\n" + "="*60)
    print("ANÁLISIS DE DUPLICADOS")
    print("="*60)
    
    # Duplicados por RUT
    ruts_no_vacios = df_salida[df_salida['RUT'] != '']
    duplicados_rut = ruts_no_vacios[ruts_no_vacios.duplicated(subset=['RUT'], keep=False)]


if __name__ == "__main__":
    procesar_datos_pawer()
