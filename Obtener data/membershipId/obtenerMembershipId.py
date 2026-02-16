import pandas as pd
import sys
from pathlib import Path

# Agregar el path para importar desde utils
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils.selector_archivo import seleccionar_archivo

# Verificar si openpyxl está instalado para archivos Excel
try:
    import openpyxl
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False
    print("⚠️  Advertencia: openpyxl no está instalado. Los archivos Excel (.xlsx) no podrán ser leídos.")
    print("   Para instalar: pip install openpyxl\n")

def obtener_membershipids_activos(archivo_csv):
    """
    Lee un archivo CSV o Excel y extrae todos los MembershipIds de cuentas activas.
    
    Args:
        archivo_csv: Ruta del archivo CSV o Excel a procesar.
    
    Returns:
        Lista de MembershipIds activos.
    """
    archivo_path = Path(archivo_csv)
    extension = archivo_path.suffix.lower()
    df = None
    
    try:
        # Detectar el tipo de archivo y leerlo apropiadamente
        if extension == '.xlsx' or extension == '.xls':
            print(f"📊 Detectado archivo Excel (.{extension[1:]})")
            
            if not EXCEL_AVAILABLE:
                print(f"❌ Error: No se puede leer archivos Excel sin la biblioteca 'openpyxl'")
                print(f"   Instala con: pip install openpyxl")
                return None
            
            # Primero, ver qué hojas tiene el archivo
            excel_file = pd.ExcelFile(archivo_csv)
            print(f"📋 Hojas disponibles: {', '.join(excel_file.sheet_names)}")
            
            # Leer la primera hoja por defecto, o permitir seleccionar
            if len(excel_file.sheet_names) > 1:
                print(f"\n⚠️  El archivo tiene múltiples hojas. Leyendo la primera: '{excel_file.sheet_names[0]}'")
            
            df = pd.read_excel(archivo_csv, sheet_name=0)
            print(f"✅ Archivo Excel leído exitosamente")
            
        elif extension == '.csv':
            print(f"📊 Detectado archivo CSV")
            
            # Lista de encodings a intentar para CSV
            encodings = ['utf-8', 'latin-1', 'windows-1252', 'iso-8859-1', 'cp1252']
            encoding_usado = None
            
            # Intentar leer con diferentes encodings
            for encoding in encodings:
                try:
                    df = pd.read_csv(archivo_csv, encoding=encoding)
                    encoding_usado = encoding
                    print(f"✅ Archivo CSV leído exitosamente con encoding: {encoding}")
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    continue
            
            if df is None:
                print(f"❌ No se pudo leer el archivo CSV con ninguno de los encodings probados")
                return None
        else:
            print(f"❌ Tipo de archivo no soportado: {extension}")
            print(f"   Tipos soportados: .csv, .xlsx, .xls")
            return None
        
        # Mostrar información del DataFrame
        print(f"\n📊 Información del archivo:")
        print(f"   - Filas: {len(df)}")
        print(f"   - Columnas: {len(df.columns)}")
        print(f"\n📋 Columnas encontradas:")
        for i, col in enumerate(df.columns, 1):
            print(f"   {i}. {col}")
        
        # Validar que las columnas necesarias existan
        columnas_requeridas = ['Estado de la membresía', 'MembershipId']
        columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
        
        if columnas_faltantes:
            print(f"\n❌ Error: Las siguientes columnas no se encontraron en el archivo:")
            for col in columnas_faltantes:
                print(f"   - {col}")
            return None
        
        # Filtrar solo las membresías activas
        df_activos = df[df['Estado de la membresía'] == 'Activo']
        
        print(f"\n✅ Membresías activas encontradas: {len(df_activos)}")
        
        # Obtener la lista de MembershipIds
        membershipids = df_activos['MembershipId'].tolist()
        
        # Eliminar valores nulos o vacíos
        membershipids = [str(mid) for mid in membershipids if pd.notna(mid) and str(mid).strip()]
        
        return membershipids
    
    except Exception as e:
        print(f"❌ Error al procesar el archivo: {e}")
        import traceback
        traceback.print_exc()
        return None

def formatear_membershipids(membershipids):
    """
    Formatea la lista de MembershipIds en el formato requerido.
    
    Args:
        membershipids: Lista de MembershipIds.
    
    Returns:
        String formateado con los MembershipIds.
    """
    if not membershipids:
        return ""
    
    # Formatear cada ID con comillas
    ids_formateados = [f'"{mid}"' for mid in membershipids]
    
    # Unir con comas y saltos de línea
    resultado = ",\n".join(ids_formateados)
    
    return resultado

def guardar_resultado(contenido, nombre_archivo="membershipIds_activos.txt"):
    """
    Guarda el resultado en un archivo de texto.
    
    Args:
        contenido: Contenido a guardar.
        nombre_archivo: Nombre del archivo de salida.
    """
    try:
        # Obtener la ruta del directorio actual
        directorio_actual = Path(__file__).parent
        ruta_salida = directorio_actual / nombre_archivo
        
        with open(ruta_salida, 'w', encoding='utf-8') as f:
            f.write(contenido)
        
        print(f"\n✅ Resultado guardado en: {ruta_salida}")
        return ruta_salida
    
    except Exception as e:
        print(f"❌ Error al guardar el archivo: {e}")
        return None

def main():
    print("🐾 Extractor de MembershipIds Activos\n")
    
    # Seleccionar archivo CSV o Excel
    archivo_csv = seleccionar_archivo(
        extensiones=['.csv', '.xlsx'],
        titulo="SELECTOR DE ARCHIVOS CSV/EXCEL"
    )
    
    if archivo_csv is None:
        print("\n❌ Operación cancelada por el usuario.")
        return
    
    print("\n" + "=" * 60)
    print(f"📄 Archivo seleccionado: {archivo_csv}")
    print("=" * 60 + "\n")
    
    print("📊 Procesando archivo...")
    
    # Obtener los MembershipIds activos
    membershipids = obtener_membershipids_activos(archivo_csv)
    
    if membershipids is None:
        return
    
    if not membershipids:
        print("\n⚠️  No se encontraron membresías activas en el archivo.")
        return
    
    print(f"\n✅ Se encontraron {len(membershipids)} membresías activas")
    
    # Formatear los MembershipIds
    resultado_formateado = formatear_membershipids(membershipids)
    
    # Mostrar una vista previa
    print("\n" + "=" * 60)
    print("📋 Vista previa del resultado:")
    print("=" * 60)
    lineas = resultado_formateado.split('\n')
    if len(lineas) <= 10:
        print(resultado_formateado)
    else:
        # Mostrar solo las primeras 5 y últimas 5 líneas
        print('\n'.join(lineas[:5]))
        print(f"... ({len(lineas) - 10} líneas más) ...")
        print('\n'.join(lineas[-5:]))
    print("=" * 60)
    
    # Guardar el resultado
    ruta_guardada = guardar_resultado(resultado_formateado)
    
    if ruta_guardada:
        print(f"\n📝 Total de MembershipIds procesados: {len(membershipids)}")
        print("\n🎉 Proceso completado exitosamente!")

if __name__ == "__main__":
    main()
