"""
Script para procesar datos de Pyme y generar archivos separados por estado activo.

Lee el archivo CSV de Pyme y genera dos archivos:
- Activos: con formato Nombre, Apellido, Email, RUT
- Inactivos: con toda la data completa

El archivo de entrada debe estar en la carpeta 'data':
'20260105_PAWER Asistencia de Mascotas_FULL_Pawer_asist - Pyme.csv'

Formato del CSV de Pyme:
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


def procesar_datos_pyme():
    """
    Procesa el archivo CSV de Pyme y genera archivos según el formato requerido.
    """
    # Rutas de archivos
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    
    # Buscar el archivo en la carpeta data
    archivo_entrada = buscar_archivo_en_data(base_dir, ['PAWER', 'Pyme'])
    
    if not archivo_entrada:
        # Intentar buscar directamente el nombre específico
        archivo_entrada = os.path.join(base_dir, 'data', '20260105_PAWER Asistencia de Mascotas_FULL_Pawer_asist - Pyme.csv')
        if not os.path.exists(archivo_entrada):
            print(f"Error: No se encontró el archivo de datos de Pyme en {os.path.join(base_dir, 'data')}")
            print("Buscando archivo que contenga 'PAWER' y 'Pyme'")
            return
    
    # Carpeta de salida
    resultado_dir = asegurar_directorio_resultado(base_dir)
    archivo_activos = os.path.join(resultado_dir, 'datos_pyme_activos.csv')
    archivo_inactivos = os.path.join(resultado_dir, 'datos_pyme_inactivos.xlsx')
    
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
            'activo': ['Estado', 'ESTADO', 'Activo']
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
        columnas_faltantes = [k for k in ['nombre', 'apellido_paterno', 'apellido_materno', 'rut', 'dv', 'email'] 
                            if k not in columnas_reales]
        if columnas_faltantes:
            print(f"Advertencia: No se encontraron las siguientes columnas: {columnas_faltantes}")
            print("Se usarán valores vacíos para estas columnas.")
        
        # Separar datos por estado activo (si existe la columna)
        col_activo = columnas_reales.get('activo')
        df_activos, df_inactivos = separar_por_activo(df, col_activo)
        
        if col_activo:
            print(f"\nRegistros activos: {len(df_activos)}")
            print(f"Registros inactivos: {len(df_inactivos)}")
        else:
            print(f"\nAdvertencia: No se encontró la columna 'Estado/Activo'. Se procesarán todos los {len(df_activos)} registros como activos.")
        
        # ===== PROCESAR ACTIVOS (formato simplificado) =====
        df_activos_salida = pd.DataFrame()
        
        # Nombre (normalizado con primera letra en mayúscula)
        if 'nombre' in columnas_reales:
            df_activos_salida['Nombre'] = df_activos[columnas_reales['nombre']].fillna('').apply(normalizar_nombre)
        else:
            df_activos_salida['Nombre'] = ''
        
        # Apellido (combinar paterno y materno, normalizado)
        apellido_paterno = df_activos[columnas_reales['apellido_paterno']].fillna('').apply(normalizar_nombre) if 'apellido_paterno' in columnas_reales else pd.Series([''] * len(df_activos))
        apellido_materno = df_activos[columnas_reales['apellido_materno']].fillna('').apply(normalizar_nombre) if 'apellido_materno' in columnas_reales else pd.Series([''] * len(df_activos))
        
        df_activos_salida['Apellido'] = [combinar_apellidos(p, m) for p, m in zip(apellido_paterno, apellido_materno)]
        
        # Email (normalizado a minúsculas)
        if 'email' in columnas_reales:
            df_activos_salida['Email'] = df_activos[columnas_reales['email']].fillna('').apply(normalizar_email)
        else:
            df_activos_salida['Email'] = ''
        
        # Asignar correos ficticios a los registros sin email
        correo_ficticio_counter = 1
        for idx in df_activos_salida.index:
            if df_activos_salida.loc[idx, 'Email'] == '' or df_activos_salida.loc[idx, 'Email'].strip() == '':
                df_activos_salida.loc[idx, 'Email'] = f'correo-ficticio-{correo_ficticio_counter}@sincorreo.com'
                correo_ficticio_counter += 1
        
        # RUT (combinar RUT y DV sin puntos ni guión)
        if 'rut' in columnas_reales and 'dv' in columnas_reales:
            rut_series = df_activos[columnas_reales['rut']].fillna('')
            dv_series = df_activos[columnas_reales['dv']].fillna('')
            df_activos_salida['RUT'] = [combinar_rut_dv(r, d) for r, d in zip(rut_series, dv_series)]
        elif 'rut' in columnas_reales:
            df_activos_salida['RUT'] = df_activos[columnas_reales['rut']].fillna('').astype(str)
        else:
            df_activos_salida['RUT'] = ''
        
        # Guardar archivo de activos en formato CSV personalizado
        guardar_csv_formato_especial(df_activos_salida, archivo_activos)
        
        print(f"\nArchivo de activos guardado en: {archivo_activos}")
        print(f"Registros activos procesados: {len(df_activos_salida)}")
        
        # ===== DETECTAR Y REPORTAR DUPLICADOS =====
        print("\n" + "="*60)
        print("ANÁLISIS DE DUPLICADOS")
        print("="*60)
        
        # Duplicados por RUT
        ruts_no_vacios = df_activos_salida[df_activos_salida['RUT'] != '']
        duplicados_rut = ruts_no_vacios[ruts_no_vacios.duplicated(subset=['RUT'], keep=False)]
        
        if len(duplicados_rut) > 0:
            print(f"\n⚠ Se encontraron {len(duplicados_rut)} registros con RUT duplicado:")
            duplicados_rut_agrupados = duplicados_rut.groupby('RUT').size().sort_values(ascending=False)
            print(f"  Total de RUTs únicos duplicados: {len(duplicados_rut_agrupados)}")
            print("\nRUTs más repetidos:")
            for rut, count in duplicados_rut_agrupados.head(10).items():
                print(f"  - RUT {rut}: {count} veces")
                registros = duplicados_rut[duplicados_rut['RUT'] == rut][['Nombre', 'Apellido', 'Email']]
                for idx, row in registros.iterrows():
                    print(f"    • {row['Nombre']} {row['Apellido']} - {row['Email']}")
        else:
            print("\n✓ No se encontraron RUTs duplicados")
        
        # Duplicados por Email
        emails_no_vacios = df_activos_salida[df_activos_salida['Email'] != '']
        duplicados_email = emails_no_vacios[emails_no_vacios.duplicated(subset=['Email'], keep=False)]
        
        if len(duplicados_email) > 0:
            print(f"\n⚠ Se encontraron {len(duplicados_email)} registros con Email duplicado:")
            duplicados_email_agrupados = duplicados_email.groupby('Email').size().sort_values(ascending=False)
            print(f"  Total de Emails únicos duplicados: {len(duplicados_email_agrupados)}")
            print("\nEmails más repetidos:")
            for email, count in duplicados_email_agrupados.head(10).items():
                print(f"  - Email {email}: {count} veces")
                registros = duplicados_email[duplicados_email['Email'] == email][['Nombre', 'Apellido', 'RUT']]
                for idx, row in registros.iterrows():
                    print(f"    • {row['Nombre']} {row['Apellido']} - RUT: {row['RUT']}")
        else:
            print("\n✓ No se encontraron Emails duplicados")
        
        print("\n" + "="*60)
        
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
    procesar_datos_pyme()
