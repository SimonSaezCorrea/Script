"""
Script para comparar datos entre archivo de carga PAWER y archivos BICE (OMG + Pyme).

Compara RUTs y reporta inconsistencias, separando entre empresas OMG y Pyme.

Archivos:
- 20260127_PAWER Asistencia de Mascotas_FULL_Pawer_asist.xlsx (CARGA)
- BICE OMG Convenio_users_28_01_2026.xlsx (BICE OMG)
- BICE PYME_users_28_01_2026.xlsx (BICE PYME)

Empresas OMG:
- DDB CHILE SPA
- INFLUENCE & RESEARCH S.A.
- MEDIA INTERACTIVE S A
- OMD CHILE SPA
- OMNICOM MEDIA GROUP CHILE S.A.
- PHD CHILE S.A.

Todas las demás empresas son Pyme.
"""
import pandas as pd
import os
import sys
from datetime import datetime

# Agregar la carpeta padre al path para poder importar utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.normalizers import combinar_rut_dv
from utils.file_handlers import buscar_archivo_en_data


# Empresas que pertenecen a OMG
EMPRESAS_OMG = [
    'DDB CHILE SPA',
    'INFLUENCE & RESEARCH S.A.',
    'MEDIA INTERACTIVE S A',
    'OMD CHILE SPA',
    'OMNICOM MEDIA GROUP CHILE S.A.',
    'PHD CHILE S.A.'
]


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


def es_empresa_omg(nombre_empresa):
    """
    Verifica si una empresa pertenece al grupo OMG.
    """
    if not nombre_empresa or pd.isna(nombre_empresa):
        return False
    
    nombre_upper = str(nombre_empresa).upper().strip()
    
    for empresa in EMPRESAS_OMG:
        if empresa.upper() in nombre_upper:
            return True
    
    return False


def generar_email_unico(email_base, emails_existentes):
    """
    Genera un email único agregando -copy, --copy, ---copy, etc.
    hasta que no exista en el conjunto de emails existentes.
    
    Args:
        email_base: Email original
        emails_existentes: Set de emails que ya existen
    
    Returns:
        Email único
    """
    if not email_base or pd.isna(email_base) or str(email_base).strip() == '':
        return email_base
    
    email_base = str(email_base).strip().lower()
    
    # Si no existe, retornar tal cual
    if email_base not in emails_existentes:
        return email_base
    
    # Si existe, agregar -copy, --copy, ---copy, etc.
    contador = 1
    while True:
        prefijo = '-' * contador + 'copy'
        
        # Separar nombre y dominio
        if '@' in email_base:
            nombre, dominio = email_base.rsplit('@', 1)
            email_nuevo = f"{nombre}{prefijo}@{dominio}"
        else:
            email_nuevo = f"{email_base}{prefijo}"
        
        # Verificar si este nuevo email existe
        if email_nuevo not in emails_existentes:
            return email_nuevo
        
        contador += 1
        
        # Seguridad: si llega a 100, algo está mal
        if contador > 100:
            print(f"  ⚠️  Warning: Email {email_base} generó más de 100 copias")
            return email_nuevo


def comparar_pyme_bice():
    """
    Compara los RUTs entre el archivo de carga y los archivos BICE (OMG + Pyme).
    """
    # Rutas de archivos
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, 'data', 'Pyme')
    
    # Buscar archivos dinámicamente
    archivo_carga = None
    archivo_bice_omg = None
    archivo_bice_pyme = None
    
    for filename in os.listdir(data_dir):
        # Ignorar archivos temporales de Excel
        if filename.startswith('~$'):
            continue
            
        if 'PAWER Asistencia de Mascotas' in filename and filename.endswith('.xlsx'):
            archivo_carga = os.path.join(data_dir, filename)
        elif 'BICE OMG Convenio' in filename:
            archivo_bice_omg = os.path.join(data_dir, filename)
        elif 'BICE PYME' in filename and 'OMG' not in filename:
            archivo_bice_pyme = os.path.join(data_dir, filename)
    
    if not archivo_carga or not archivo_bice_omg or not archivo_bice_pyme:
        print("❌ Error: No se encontraron todos los archivos necesarios")
        print(f"   Carga encontrado: {archivo_carga is not None}")
        print(f"   BICE OMG encontrado: {archivo_bice_omg is not None}")
        print(f"   BICE Pyme encontrado: {archivo_bice_pyme is not None}")
        return
    
    print("="*80)
    print("📊 COMPARACIÓN CARGA vs BICE (OMG + PYME)")
    print("="*80)
    print(f"\nArchivo Carga: {os.path.basename(archivo_carga)}")
    print(f"Archivo BICE OMG: {os.path.basename(archivo_bice_omg)}")
    print(f"Archivo BICE Pyme: {os.path.basename(archivo_bice_pyme)}")
    
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
    
    # Leer BICE OMG (Excel)
    df_bice_omg = pd.read_excel(archivo_bice_omg)
    print(f"  ✓ Archivo BICE OMG leído correctamente")
    
    # Leer BICE Pyme (Excel)
    df_bice_pyme = pd.read_excel(archivo_bice_pyme)
    print(f"  ✓ Archivo BICE Pyme leído correctamente")
    
    print(f"\n📈 Registros totales:")
    print(f"  - Carga: {len(df_carga)}")
    print(f"  - BICE OMG (total): {len(df_bice_omg)}")
    print(f"  - BICE Pyme (total): {len(df_bice_pyme)}")
    
    # Filtrar solo registros con Estado = VERDADERO en archivos BICE
    if 'Estado' in df_bice_omg.columns:
        df_bice_omg['Estado'] = df_bice_omg['Estado'].astype(str).str.upper()
        df_bice_omg = df_bice_omg[df_bice_omg['Estado'].isin(['VERDADERO', 'TRUE', 'ACTIVO', '1'])].copy()
        print(f"  - BICE OMG (activos): {len(df_bice_omg)}")
    
    if 'Estado' in df_bice_pyme.columns:
        df_bice_pyme['Estado'] = df_bice_pyme['Estado'].astype(str).str.upper()
        df_bice_pyme = df_bice_pyme[df_bice_pyme['Estado'].isin(['VERDADERO', 'TRUE', 'ACTIVO', '1'])].copy()
        print(f"  - BICE Pyme (activos): {len(df_bice_pyme)}")
    
    # Filtrar solo los activos (Estado = VERDADERO) en archivos BICE
    print(f"\n🔍 Filtrando registros activos (Estado = VERDADERO)...")
    
    if 'Estado' in df_bice_omg.columns:
        antes_omg = len(df_bice_omg)
        df_bice_omg = df_bice_omg[df_bice_omg['Estado'].apply(
            lambda x: str(x).upper() in ['TRUE', 'VERDADERO', 'SI', 'SÍ', 'YES', '1', 'ACTIVO']
        )].copy()
        print(f"  ✓ BICE OMG: {len(df_bice_omg)} activos de {antes_omg} totales ({antes_omg - len(df_bice_omg)} inactivos filtrados)")
    else:
        print(f"  ⚠️  BICE OMG: No se encontró columna 'Estado', usando todos los registros")
    
    if 'Estado' in df_bice_pyme.columns:
        antes_pyme = len(df_bice_pyme)
        df_bice_pyme = df_bice_pyme[df_bice_pyme['Estado'].apply(
            lambda x: str(x).upper() in ['TRUE', 'VERDADERO', 'SI', 'SÍ', 'YES', '1', 'ACTIVO']
        )].copy()
        print(f"  ✓ BICE Pyme: {len(df_bice_pyme)} activos de {antes_pyme} totales ({antes_pyme - len(df_bice_pyme)} inactivos filtrados)")
    else:
        print(f"  ⚠️  BICE Pyme: No se encontró columna 'Estado', usando todos los registros")
    
    # Procesar RUTs en Carga
    print("\n🔧 Procesando RUTs...")
    
    # Combinar RUT_ASEGURADO + DV_ASEGURADO en archivo de carga
    if 'RUT_ASEGURADO' in df_carga.columns and 'DV_ASEGURADO' in df_carga.columns:
        df_carga['RUT_COMPLETO'] = df_carga.apply(
            lambda row: combinar_rut_dv(row['RUT_ASEGURADO'], row['DV_ASEGURADO']), 
            axis=1
        )
    else:
        print("❌ Error: No se encontraron columnas RUT_ASEGURADO y DV_ASEGURADO en archivo de carga")
        return
    
    # Normalizar RUTs
    df_carga['RUT_NORM'] = df_carga['RUT_COMPLETO'].apply(normalizar_rut_comparacion)
    df_bice_omg['RUT_NORM'] = df_bice_omg['RUT'].apply(normalizar_rut_comparacion)
    df_bice_pyme['RUT_NORM'] = df_bice_pyme['RUT'].apply(normalizar_rut_comparacion)
    
    # Eliminar RUTs vacíos
    df_carga = df_carga[df_carga['RUT_NORM'] != ''].copy()
    df_bice_omg = df_bice_omg[df_bice_omg['RUT_NORM'] != ''].copy()
    df_bice_pyme = df_bice_pyme[df_bice_pyme['RUT_NORM'] != ''].copy()
    
    print(f"  ✓ RUTs válidos: Carga={len(df_carga)}, BICE OMG={len(df_bice_omg)}, BICE Pyme={len(df_bice_pyme)}")
    
    # Separar OMG de Pyme en archivo de carga según NOMBRE_CONTRATANTE
    print("\n🏢 Clasificando empresas en archivo de carga...")
    
    df_carga['ES_OMG'] = df_carga['NOMBRE_CONTRATANTE'].apply(es_empresa_omg)
    
    df_carga_omg = df_carga[df_carga['ES_OMG'] == True].copy()
    df_carga_pyme = df_carga[df_carga['ES_OMG'] == False].copy()
    
    print(f"  ✓ Registros OMG en Carga: {len(df_carga_omg)}")
    print(f"  ✓ Registros Pyme en Carga: {len(df_carga_pyme)}")
    
    # Obtener sets de RUTs únicos
    ruts_carga_omg = set(df_carga_omg['RUT_NORM'].unique())
    ruts_carga_pyme = set(df_carga_pyme['RUT_NORM'].unique())
    ruts_bice_omg = set(df_bice_omg['RUT_NORM'].unique())
    ruts_bice_pyme = set(df_bice_pyme['RUT_NORM'].unique())
    
    print(f"\n🔢 RUTs únicos:")
    print(f"  - OMG en Carga: {len(ruts_carga_omg)}")
    print(f"  - Pyme en Carga: {len(ruts_carga_pyme)}")
    print(f"  - BICE OMG: {len(ruts_bice_omg)}")
    print(f"  - BICE Pyme: {len(ruts_bice_pyme)}")
    
    # Realizar comparaciones
    print("\n🔍 Realizando comparaciones...")
    
    # Comparaciones OMG
    # 1. RUTs de OMG en Carga que coinciden con BICE OMG
    omg_coincidencias = ruts_carga_omg & ruts_bice_omg
    
    # 2. RUTs de OMG en Carga que NO están en BICE OMG
    omg_carga_no_en_bice = ruts_carga_omg - ruts_bice_omg
    
    # 3. RUTs en BICE OMG que NO están en Carga OMG
    omg_bice_no_en_carga = ruts_bice_omg - ruts_carga_omg
    
    # Comparaciones Pyme
    # 4. RUTs de Pyme en Carga que coinciden con BICE Pyme
    pyme_coincidencias = ruts_carga_pyme & ruts_bice_pyme
    
    # 5. RUTs de Pyme en Carga que NO están en BICE Pyme
    pyme_carga_no_en_bice = ruts_carga_pyme - ruts_bice_pyme
    
    # 6. RUTs en BICE Pyme que NO están en Carga Pyme
    pyme_bice_no_en_carga = ruts_bice_pyme - ruts_carga_pyme
    
    # Errores de clasificación
    # 7. RUTs de Pyme en Carga que aparecen en BICE OMG (error)
    pyme_en_bice_omg = ruts_carga_pyme & ruts_bice_omg
    
    # 8. RUTs de OMG en Carga que aparecen en BICE Pyme (error)
    omg_en_bice_pyme = ruts_carga_omg & ruts_bice_pyme
    
    # Detectar diferencias de cantidad
    print("\n🔢 Detectando diferencias de cantidad por RUT...")
    diferencias_cantidad_omg = []
    for rut in omg_coincidencias:
        cantidad_carga = len(df_carga_omg[df_carga_omg['RUT_NORM'] == rut])
        cantidad_bice = len(df_bice_omg[df_bice_omg['RUT_NORM'] == rut])
        if cantidad_carga != cantidad_bice:
            diferencias_cantidad_omg.append({
                'rut': rut,
                'cantidad_carga': cantidad_carga,
                'cantidad_bice': cantidad_bice
            })
    
    diferencias_cantidad_pyme = []
    for rut in pyme_coincidencias:
        cantidad_carga = len(df_carga_pyme[df_carga_pyme['RUT_NORM'] == rut])
        cantidad_bice = len(df_bice_pyme[df_bice_pyme['RUT_NORM'] == rut])
        if cantidad_carga != cantidad_bice:
            diferencias_cantidad_pyme.append({
                'rut': rut,
                'cantidad_carga': cantidad_carga,
                'cantidad_bice': cantidad_bice
            })
    
    print("\n" + "="*80)
    print("📊 RESULTADOS DE LA COMPARACIÓN")
    print("="*80)
    
    print(f"\n✅ COINCIDENCIAS:")
    print(f"  - OMG (Carga OMG = BICE OMG): {len(omg_coincidencias)}")
    print(f"  - Pyme (Carga Pyme = BICE Pyme): {len(pyme_coincidencias)}")
    print(f"  - TOTAL COINCIDENCIAS: {len(omg_coincidencias) + len(pyme_coincidencias)}")
    
    print(f"\n⚠️  INCONSISTENCIAS:")
    print(f"  OMG:")
    print(f"    1. RUTs OMG en Carga pero NO en BICE OMG: {len(omg_carga_no_en_bice)}")
    print(f"    2. RUTs en BICE OMG pero NO en Carga OMG: {len(omg_bice_no_en_carga)}")
    print(f"    3. RUTs OMG con diferente cantidad de registros: {len(diferencias_cantidad_omg)}")
    print(f"  Pyme:")
    print(f"    4. RUTs Pyme en Carga pero NO en BICE Pyme: {len(pyme_carga_no_en_bice)}")
    print(f"    5. RUTs en BICE Pyme pero NO en Carga Pyme: {len(pyme_bice_no_en_carga)}")
    print(f"    6. RUTs Pyme con diferente cantidad de registros: {len(diferencias_cantidad_pyme)}")
    print(f"  Errores de clasificación:")
    print(f"    7. RUTs Pyme en Carga que aparecen en BICE OMG: {len(pyme_en_bice_omg)}")
    print(f"    8. RUTs OMG en Carga que aparecen en BICE Pyme: {len(omg_en_bice_pyme)}")
    
    # Crear DataFrames de resultados
    resultados = []
    
    # 1. Coincidencias OMG (con cantidad correcta)
    ruts_omg_con_diferencia = set([d['rut'] for d in diferencias_cantidad_omg])
    for rut in omg_coincidencias:
        if rut in ruts_omg_con_diferencia:
            continue  # Se procesarán después
        
        reg_carga = df_carga_omg[df_carga_omg['RUT_NORM'] == rut].iloc[0]
        reg_bice = df_bice_omg[df_bice_omg['RUT_NORM'] == rut].iloc[0]
        cantidad_carga = len(df_carga_omg[df_carga_omg['RUT_NORM'] == rut])
        cantidad_bice = len(df_bice_omg[df_bice_omg['RUT_NORM'] == rut])
        
        resultados.append({
            'RUT': rut,
            'ESTADO': 'COINCIDENCIA_OMG',
            'TIPO': 'OMG',
            'EMPRESA_CARGA': reg_carga.get('NOMBRE_CONTRATANTE', ''),
            'NOMBRE_CARGA': reg_carga.get('NOMBRE CARGA', ''),
            'NOMBRE_BICE': reg_bice.get('Nombre', ''),
            'APELLIDO_BICE': reg_bice.get('Apellido', ''),
            'EMAIL_BICE': reg_bice.get('Email', ''),
            'CANTIDAD_CARGA': cantidad_carga,
            'CANTIDAD_BICE': cantidad_bice,
            'OBSERVACION': 'OK - RUT OMG presente en ambos archivos'
        })
    
    # 1b. Diferencias de cantidad OMG
    for diff in diferencias_cantidad_omg:
        rut = diff['rut']
        reg_carga = df_carga_omg[df_carga_omg['RUT_NORM'] == rut].iloc[0]
        reg_bice = df_bice_omg[df_bice_omg['RUT_NORM'] == rut].iloc[0]
        
        resultados.append({
            'RUT': rut,
            'ESTADO': 'DIFERENCIA_CANTIDAD_OMG',
            'TIPO': 'OMG',
            'EMPRESA_CARGA': reg_carga.get('NOMBRE_CONTRATANTE', ''),
            'NOMBRE_CARGA': reg_carga.get('NOMBRE CARGA', ''),
            'NOMBRE_BICE': reg_bice.get('Nombre', ''),
            'APELLIDO_BICE': reg_bice.get('Apellido', ''),
            'EMAIL_BICE': reg_bice.get('Email', ''),
            'CANTIDAD_CARGA': diff['cantidad_carga'],
            'CANTIDAD_BICE': diff['cantidad_bice'],
            'OBSERVACION': f"DIFERENCIA OMG - Carga tiene {diff['cantidad_carga']} registros, BICE tiene {diff['cantidad_bice']} registros"
        })
    
    # 2. Coincidencias Pyme (con cantidad correcta)
    ruts_pyme_con_diferencia = set([d['rut'] for d in diferencias_cantidad_pyme])
    for rut in pyme_coincidencias:
        if rut in ruts_pyme_con_diferencia:
            continue  # Se procesarán después
        
        reg_carga = df_carga_pyme[df_carga_pyme['RUT_NORM'] == rut].iloc[0]
        reg_bice = df_bice_pyme[df_bice_pyme['RUT_NORM'] == rut].iloc[0]
        cantidad_carga = len(df_carga_pyme[df_carga_pyme['RUT_NORM'] == rut])
        cantidad_bice = len(df_bice_pyme[df_bice_pyme['RUT_NORM'] == rut])
        
        resultados.append({
            'RUT': rut,
            'ESTADO': 'COINCIDENCIA_PYME',
            'TIPO': 'PYME',
            'EMPRESA_CARGA': reg_carga.get('NOMBRE_CONTRATANTE', ''),
            'NOMBRE_CARGA': reg_carga.get('NOMBRE CARGA', ''),
            'NOMBRE_BICE': reg_bice.get('Nombre', ''),
            'APELLIDO_BICE': reg_bice.get('Apellido', ''),
            'EMAIL_BICE': reg_bice.get('Email', ''),
            'CANTIDAD_CARGA': cantidad_carga,
            'CANTIDAD_BICE': cantidad_bice,
            'OBSERVACION': 'OK - RUT Pyme presente en ambos archivos'
        })
    
    # 2b. Diferencias de cantidad Pyme
    for diff in diferencias_cantidad_pyme:
        rut = diff['rut']
        reg_carga = df_carga_pyme[df_carga_pyme['RUT_NORM'] == rut].iloc[0]
        reg_bice = df_bice_pyme[df_bice_pyme['RUT_NORM'] == rut].iloc[0]
        
        resultados.append({
            'RUT': rut,
            'ESTADO': 'DIFERENCIA_CANTIDAD_PYME',
            'TIPO': 'PYME',
            'EMPRESA_CARGA': reg_carga.get('NOMBRE_CONTRATANTE', ''),
            'NOMBRE_CARGA': reg_carga.get('NOMBRE CARGA', ''),
            'NOMBRE_BICE': reg_bice.get('Nombre', ''),
            'APELLIDO_BICE': reg_bice.get('Apellido', ''),
            'EMAIL_BICE': reg_bice.get('Email', ''),
            'CANTIDAD_CARGA': diff['cantidad_carga'],
            'CANTIDAD_BICE': diff['cantidad_bice'],
            'OBSERVACION': f"DIFERENCIA PYME - Carga tiene {diff['cantidad_carga']} registros, BICE tiene {diff['cantidad_bice']} registros"
        })
    
    # 3. OMG en Carga pero no en BICE
    for rut in omg_carga_no_en_bice:
        reg_carga = df_carga_omg[df_carga_omg['RUT_NORM'] == rut].iloc[0]
        
        resultados.append({
            'RUT': rut,
            'ESTADO': 'CARGA_OMG_SIN_BICE',
            'TIPO': 'OMG',
            'EMPRESA_CARGA': reg_carga.get('NOMBRE_CONTRATANTE', ''),
            'NOMBRE_CARGA': reg_carga.get('NOMBRE CARGA', ''),
            'PATERNO': reg_carga.get('PATERNO', ''),
            'MATERNO': reg_carga.get('MATERNO', ''),
            'CORREO': reg_carga.get('CORREO', ''),
            'NOMBRE_BICE': '',
            'APELLIDO_BICE': '',
            'EMAIL_BICE': '',
            'OBSERVACION': 'FALTA - RUT OMG en Carga pero NO en BICE OMG'
        })
    
    # 4. OMG en BICE pero no en Carga
    for rut in omg_bice_no_en_carga:
        reg_bice = df_bice_omg[df_bice_omg['RUT_NORM'] == rut].iloc[0]
        
        resultados.append({
            'RUT': rut,
            'ESTADO': 'BICE_OMG_SIN_CARGA',
            'TIPO': 'OMG',
            'EMPRESA_CARGA': '',
            'NOMBRE_CARGA': '',
            'NOMBRE_BICE': reg_bice.get('Nombre', ''),
            'APELLIDO_BICE': reg_bice.get('Apellido', ''),
            'EMAIL_BICE': reg_bice.get('Email', ''),
            'OBSERVACION': 'EXTRA - RUT en BICE OMG pero NO en Carga OMG'
        })
    
    # 5. Pyme en Carga pero no en BICE
    for rut in pyme_carga_no_en_bice:
        reg_carga = df_carga_pyme[df_carga_pyme['RUT_NORM'] == rut].iloc[0]
        
        resultados.append({
            'RUT': rut,
            'ESTADO': 'CARGA_PYME_SIN_BICE',
            'TIPO': 'PYME',
            'EMPRESA_CARGA': reg_carga.get('NOMBRE_CONTRATANTE', ''),
            'NOMBRE_CARGA': reg_carga.get('NOMBRE CARGA', ''),
            'PATERNO': reg_carga.get('PATERNO', ''),
            'MATERNO': reg_carga.get('MATERNO', ''),
            'CORREO': reg_carga.get('CORREO', ''),
            'NOMBRE_BICE': '',
            'APELLIDO_BICE': '',
            'EMAIL_BICE': '',
            'OBSERVACION': 'FALTA - RUT PYME en Carga pero NO en BICE PYME'
        })
    
    # 6. Pyme en BICE pero no en Carga
    for rut in pyme_bice_no_en_carga:
        reg_bice = df_bice_pyme[df_bice_pyme['RUT_NORM'] == rut].iloc[0]
        
        resultados.append({
            'RUT': rut,
            'ESTADO': 'BICE_PYME_SIN_CARGA',
            'TIPO': 'PYME',
            'EMPRESA_CARGA': '',
            'NOMBRE_CARGA': '',
            'NOMBRE_BICE': reg_bice.get('Nombre', ''),
            'APELLIDO_BICE': reg_bice.get('Apellido', ''),
            'EMAIL_BICE': reg_bice.get('Email', ''),
            'OBSERVACION': 'EXTRA - RUT en BICE Pyme pero NO en Carga Pyme'
        })
    
    # 7. Error: Pyme en Carga pero en BICE OMG
    for rut in pyme_en_bice_omg:
        reg_carga = df_carga_pyme[df_carga_pyme['RUT_NORM'] == rut].iloc[0]
        reg_bice = df_bice_omg[df_bice_omg['RUT_NORM'] == rut].iloc[0]
        
        resultados.append({
            'RUT': rut,
            'ESTADO': 'ERROR_PYME_EN_OMG',
            'TIPO': 'ERROR',
            'EMPRESA_CARGA': reg_carga.get('NOMBRE_CONTRATANTE', ''),
            'NOMBRE_CARGA': reg_carga.get('NOMBRE CARGA', ''),
            'NOMBRE_BICE': reg_bice.get('Nombre', ''),
            'APELLIDO_BICE': reg_bice.get('Apellido', ''),
            'EMAIL_BICE': reg_bice.get('Email', ''),
            'OBSERVACION': 'ERROR - RUT clasificado como Pyme en Carga pero está en BICE OMG'
        })
    
    # 8. Error: OMG en Carga pero en BICE Pyme
    for rut in omg_en_bice_pyme:
        reg_carga = df_carga_omg[df_carga_omg['RUT_NORM'] == rut].iloc[0]
        reg_bice = df_bice_pyme[df_bice_pyme['RUT_NORM'] == rut].iloc[0]
        
        resultados.append({
            'RUT': rut,
            'ESTADO': 'ERROR_OMG_EN_PYME',
            'TIPO': 'ERROR',
            'EMPRESA_CARGA': reg_carga.get('NOMBRE_CONTRATANTE', ''),
            'NOMBRE_CARGA': reg_carga.get('NOMBRE CARGA', ''),
            'NOMBRE_BICE': reg_bice.get('Nombre', ''),
            'APELLIDO_BICE': reg_bice.get('Apellido', ''),
            'EMAIL_BICE': reg_bice.get('Email', ''),
            'OBSERVACION': 'ERROR - RUT clasificado como OMG en Carga pero está en BICE Pyme'
        })
    
    # Crear DataFrame y guardar
    df_resultados = pd.DataFrame(resultados)
    
    # Ordenar por estado y RUT
    orden_estados = {
        'COINCIDENCIA_OMG': 1, 
        'COINCIDENCIA_PYME': 2, 
        'DIFERENCIA_CANTIDAD_OMG': 3,
        'DIFERENCIA_CANTIDAD_PYME': 4,
        'CARGA_OMG_SIN_BICE': 5, 
        'CARGA_PYME_SIN_BICE': 6,
        'BICE_OMG_SIN_CARGA': 7, 
        'BICE_PYME_SIN_CARGA': 8,
        'ERROR_PYME_EN_OMG': 9, 
        'ERROR_OMG_EN_PYME': 10
    }
    df_resultados['ORDEN'] = df_resultados['ESTADO'].map(orden_estados)
    df_resultados = df_resultados.sort_values(['ORDEN', 'RUT']).drop('ORDEN', axis=1)
    
    # Separar en dos DataFrames: coincidencias e inconsistencias
    df_coincidencias = df_resultados[df_resultados['ESTADO'].str.contains('COINCIDENCIA')].copy()
    df_inconsistencias = df_resultados[~df_resultados['ESTADO'].str.contains('COINCIDENCIA')].copy()
    
    # Guardar resultados
    resultado_dir = os.path.join(script_dir, 'resultado')
    os.makedirs(resultado_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Guardar archivo de coincidencias
    archivo_coincidencias = os.path.join(resultado_dir, f'comparacion_coincidencias_{timestamp}.xlsx')
    df_coincidencias.to_excel(archivo_coincidencias, index=False)
    
    # Guardar archivo de inconsistencias
    archivo_inconsistencias = os.path.join(resultado_dir, f'comparacion_inconsistencias_{timestamp}.xlsx')
    df_inconsistencias.to_excel(archivo_inconsistencias, index=False)
    
    print(f"\n💾 Resultados guardados en:")
    print(f"   📗 Coincidencias: {os.path.basename(archivo_coincidencias)}")
    print(f"   📕 Inconsistencias: {os.path.basename(archivo_inconsistencias)}")
    
    # Resumen por estado
    print("\n📋 Resumen por estado:")
    print(f"   ✅ COINCIDENCIAS: {len(df_coincidencias)}")
    if len(df_coincidencias) > 0:
        for estado, cantidad in df_coincidencias['ESTADO'].value_counts().items():
            print(f"      - {estado}: {cantidad}")
    
    print(f"   ⚠️  INCONSISTENCIAS: {len(df_inconsistencias)}")
    if len(df_inconsistencias) > 0:
        for estado, cantidad in df_inconsistencias['ESTADO'].value_counts().items():
            print(f"      - {estado}: {cantidad}")
    
    # ========================================
    # PROCESAR REGISTROS EN CARGA QUE NO ESTÁN EN BICE
    # Aplicar transformación de duplicados (agregar ceros)
    # ========================================
    print("\n" + "="*60)
    print("📋 PROCESANDO DUPLICADOS CON CEROS A LA DERECHA")
    print("="*60)
    
    from utils.file_handlers import guardar_csv_formato_especial
    resultado_dir = os.path.join(script_dir, 'resultado')
    
    # Obtener RUTs de BICE para saber cuáles ya existen
    ruts_bice_omg_existentes = set(df_bice_omg['RUT_NORM'])
    ruts_bice_pyme_existentes = set(df_bice_pyme['RUT_NORM'])
    
    # Procesar OMG
    if len(df_carga_omg) > 0:
        print(f"\n🏢 Procesando registros OMG...")
        
        # Agrupar por RUT y agregar índice de repetición
        df_carga_omg_proc = df_carga_omg.copy()
        df_carga_omg_proc['REPETICION'] = df_carga_omg_proc.groupby('RUT_NORM').cumcount()
        
        # Agregar ceros según repetición
        def agregar_ceros_por_repeticion(row):
            rut_base = row['RUT_NORM']
            repeticion = row['REPETICION']
            
            if repeticion == 0:
                return rut_base  # Primera aparición, sin cambios
            else:
                # Agregar tantos ceros como repeticiones
                return rut_base + ('0' * repeticion)
        
        df_carga_omg_proc['RUT_CON_CEROS'] = df_carga_omg_proc.apply(agregar_ceros_por_repeticion, axis=1)
        
        # Contar duplicados transformados
        duplicados_omg = df_carga_omg_proc[df_carga_omg_proc['REPETICION'] > 0]
        print(f"  ✓ Total registros OMG: {len(df_carga_omg_proc)}")
        print(f"  ✓ RUTs únicos originales: {df_carga_omg_proc['RUT_NORM'].nunique()}")
        print(f"  ✓ Duplicados transformados con ceros: {len(duplicados_omg)}")
        
        # Filtrar los que NO están en BICE OMG
        df_carga_omg_no_en_bice = df_carga_omg_proc[~df_carga_omg_proc['RUT_CON_CEROS'].isin(ruts_bice_omg_existentes)].copy()
        
        print(f"  📝 Registros OMG que NO están en BICE: {len(df_carga_omg_no_en_bice)}")
        
        if len(df_carga_omg_no_en_bice) > 0:
            # Obtener emails existentes en BICE OMG
            emails_existentes_omg = set()
            if 'Email' in df_bice_omg.columns:
                emails_existentes_omg = set(
                    df_bice_omg['Email'].dropna().astype(str).str.lower().str.strip()
                )
            
            # Generar emails únicos
            emails_procesados_omg = []
            emails_modificados_omg = 0
            
            for idx, row in df_carga_omg_no_en_bice.iterrows():
                email_original = row.get('CORREO', '')
                if pd.isna(email_original):
                    email_original = ''
                email_original = str(email_original).strip().lower()
                
                email_unico = generar_email_unico(email_original, emails_existentes_omg)
                
                if email_unico != email_original and email_original != '':
                    emails_modificados_omg += 1
                
                # Agregar a set para siguientes validaciones
                if email_unico and email_unico != '':
                    emails_existentes_omg.add(email_unico)
                emails_procesados_omg.append(email_unico)
            
            print(f"  📧 Emails OMG modificados para evitar duplicados: {emails_modificados_omg}")
            
            # Preparar DataFrame con el formato requerido
            df_csv_carga_omg = pd.DataFrame({
                'Nombre': df_carga_omg_no_en_bice['NOMBRE CARGA'].fillna('').astype(str).str.title().str.replace(r'\s+', ' ', regex=True).str.strip(),
                'Apellido': (df_carga_omg_no_en_bice['PATERNO'].fillna('').astype(str) + ' ' + df_carga_omg_no_en_bice['MATERNO'].fillna('').astype(str)).str.title().str.replace(r'\s+', ' ', regex=True).str.strip(),
                'Email': emails_procesados_omg,
                'RUT': df_carga_omg_no_en_bice['RUT_CON_CEROS']  # Usar RUT con ceros
            })
            
            # Separar registros sin email
            df_omg_sin_email = df_csv_carga_omg[df_csv_carga_omg['Email'].str.strip() == ''].copy()
            df_omg_con_email = df_csv_carga_omg[df_csv_carga_omg['Email'].str.strip() != ''].copy()
            
            # Guardar archivo principal (solo con email)
            if len(df_omg_con_email) > 0:
                archivo_csv_carga_omg = os.path.join(resultado_dir, f'carga_sin_bice_omg_{timestamp}.csv')
                guardar_csv_formato_especial(df_omg_con_email, archivo_csv_carga_omg)
                print(f"\n💾 Archivo OMG generado:")
                print(f"   📄 {os.path.basename(archivo_csv_carga_omg)} ({len(df_omg_con_email)} registros)")
                
                # Mostrar ejemplos de RUTs con ceros
                df_con_ceros_omg = df_omg_con_email[df_omg_con_email['RUT'].str.endswith('0')]
                if len(df_con_ceros_omg) > 0:
                    print(f"   📌 RUTs con ceros agregados (duplicados): {len(df_con_ceros_omg)} de {len(df_omg_con_email)}")
            
            # Guardar archivo de error (sin email)
            if len(df_omg_sin_email) > 0:
                archivo_error_omg = os.path.join(resultado_dir, f'error_carga_omg_{timestamp}.csv')
                guardar_csv_formato_especial(df_omg_sin_email, archivo_error_omg)
                print(f"   ⚠️  Error OMG sin email: {os.path.basename(archivo_error_omg)} ({len(df_omg_sin_email)} registros)")
    
    # Procesar Pyme
    if len(df_carga_pyme) > 0:
        print(f"\n🏢 Procesando registros Pyme...")
        
        # Agrupar por RUT y agregar índice de repetición
        df_carga_pyme_proc = df_carga_pyme.copy()
        df_carga_pyme_proc['REPETICION'] = df_carga_pyme_proc.groupby('RUT_NORM').cumcount()
        
        # Agregar ceros según repetición
        df_carga_pyme_proc['RUT_CON_CEROS'] = df_carga_pyme_proc.apply(agregar_ceros_por_repeticion, axis=1)
        
        # Contar duplicados transformados
        duplicados_pyme = df_carga_pyme_proc[df_carga_pyme_proc['REPETICION'] > 0]
        print(f"  ✓ Total registros Pyme: {len(df_carga_pyme_proc)}")
        print(f"  ✓ RUTs únicos originales: {df_carga_pyme_proc['RUT_NORM'].nunique()}")
        print(f"  ✓ Duplicados transformados con ceros: {len(duplicados_pyme)}")
        
        # Filtrar los que NO están en BICE Pyme
        df_carga_pyme_no_en_bice = df_carga_pyme_proc[~df_carga_pyme_proc['RUT_CON_CEROS'].isin(ruts_bice_pyme_existentes)].copy()
        
        print(f"  📝 Registros Pyme que NO están en BICE: {len(df_carga_pyme_no_en_bice)}")
        
        if len(df_carga_pyme_no_en_bice) > 0:
            # Obtener emails existentes en BICE Pyme
            emails_existentes_pyme = set()
            if 'Email' in df_bice_pyme.columns:
                emails_existentes_pyme = set(
                    df_bice_pyme['Email'].dropna().astype(str).str.lower().str.strip()
                )
            
            # Generar emails únicos
            emails_procesados_pyme = []
            emails_modificados_pyme = 0
            
            for idx, row in df_carga_pyme_no_en_bice.iterrows():
                email_original = row.get('CORREO', '')
                if pd.isna(email_original):
                    email_original = ''
                email_original = str(email_original).strip().lower()
                
                email_unico = generar_email_unico(email_original, emails_existentes_pyme)
                
                if email_unico != email_original and email_original != '':
                    emails_modificados_pyme += 1
                
                # Agregar a set para siguientes validaciones
                if email_unico and email_unico != '':
                    emails_existentes_pyme.add(email_unico)
                emails_procesados_pyme.append(email_unico)
            
            print(f"  📧 Emails Pyme modificados para evitar duplicados: {emails_modificados_pyme}")
            
            # Preparar DataFrame con el formato requerido
            df_csv_carga_pyme = pd.DataFrame({
                'Nombre': df_carga_pyme_no_en_bice['NOMBRE CARGA'].fillna('').astype(str).str.title().str.replace(r'\s+', ' ', regex=True).str.strip(),
                'Apellido': (df_carga_pyme_no_en_bice['PATERNO'].fillna('').astype(str) + ' ' + df_carga_pyme_no_en_bice['MATERNO'].fillna('').astype(str)).str.title().str.replace(r'\s+', ' ', regex=True).str.strip(),
                'Email': emails_procesados_pyme,
                'RUT': df_carga_pyme_no_en_bice['RUT_CON_CEROS']  # Usar RUT con ceros
            })
            
            # Separar registros sin email
            df_pyme_sin_email = df_csv_carga_pyme[df_csv_carga_pyme['Email'].str.strip() == ''].copy()
            df_pyme_con_email = df_csv_carga_pyme[df_csv_carga_pyme['Email'].str.strip() != ''].copy()
            
            # Guardar archivo principal (solo con email)
            if len(df_pyme_con_email) > 0:
                archivo_csv_carga_pyme = os.path.join(resultado_dir, f'carga_sin_bice_pyme_{timestamp}.csv')
                guardar_csv_formato_especial(df_pyme_con_email, archivo_csv_carga_pyme)
                print(f"\n💾 Archivo Pyme generado:")
                print(f"   📄 {os.path.basename(archivo_csv_carga_pyme)} ({len(df_pyme_con_email)} registros)")
                
                # Mostrar ejemplos de RUTs con ceros
                df_con_ceros_pyme = df_pyme_con_email[df_pyme_con_email['RUT'].str.endswith('0')]
                if len(df_con_ceros_pyme) > 0:
                    print(f"   📌 RUTs con ceros agregados (duplicados): {len(df_con_ceros_pyme)} de {len(df_pyme_con_email)}")
            
            # Guardar archivo de error (sin email)
            if len(df_pyme_sin_email) > 0:
                archivo_error_pyme = os.path.join(resultado_dir, f'error_carga_pyme_{timestamp}.csv')
                guardar_csv_formato_especial(df_pyme_sin_email, archivo_error_pyme)
                print(f"   ⚠️  Error PYME sin email: {os.path.basename(archivo_error_pyme)} ({len(df_pyme_sin_email)} registros)")
    
    # Generar CSV especial para registros en BICE que NO están en Carga
    df_bice_sin_carga_omg = df_inconsistencias[df_inconsistencias['ESTADO'] == 'BICE_OMG_SIN_CARGA'].copy()
    df_bice_sin_carga_pyme = df_inconsistencias[df_inconsistencias['ESTADO'] == 'BICE_PYME_SIN_CARGA'].copy()
    
    if len(df_bice_sin_carga_omg) > 0:
        # Preparar DataFrame OMG con el formato requerido
        df_csv_omg = pd.DataFrame({
            'Nombre': df_bice_sin_carga_omg['NOMBRE_BICE'],
            'Apellido': df_bice_sin_carga_omg['APELLIDO_BICE'],
            'Email': df_bice_sin_carga_omg['EMAIL_BICE'],
            'RUT': df_bice_sin_carga_omg['RUT']
        })
        archivo_csv_omg = os.path.join(resultado_dir, f'bice_sin_carga_omg_{timestamp}.csv')
        guardar_csv_formato_especial(df_csv_omg, archivo_csv_omg, solo_rut=True)
        print(f"   📄 BICE OMG sin Carga (formato carga): {os.path.basename(archivo_csv_omg)}")
    
    if len(df_bice_sin_carga_pyme) > 0:
        # Preparar DataFrame Pyme con el formato requerido
        df_csv_pyme = pd.DataFrame({
            'Nombre': df_bice_sin_carga_pyme['NOMBRE_BICE'],
            'Apellido': df_bice_sin_carga_pyme['APELLIDO_BICE'],
            'Email': df_bice_sin_carga_pyme['EMAIL_BICE'],
            'RUT': df_bice_sin_carga_pyme['RUT']
        })
        archivo_csv_pyme = os.path.join(resultado_dir, f'bice_sin_carga_pyme_{timestamp}.csv')
        guardar_csv_formato_especial(df_csv_pyme, archivo_csv_pyme, solo_rut=True)
        print(f"   📄 BICE Pyme sin Carga (formato carga): {os.path.basename(archivo_csv_pyme)}")
    
    # Mostrar muestras
    if len(df_inconsistencias) > 0:
        print(f"\n🔍 Muestra de inconsistencias (primeros 10):")
        print(df_inconsistencias.head(10)[['RUT', 'ESTADO', 'TIPO', 'EMPRESA_CARGA', 'NOMBRE_BICE', 'APELLIDO_BICE']].to_string(index=False))
    
    print("\n" + "="*80)
    print("✅ Proceso completado")
    print("="*80)


if __name__ == "__main__":
    comparar_pyme_bice()
