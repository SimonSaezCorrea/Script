"""
Script para comparar datos entre archivo de carga BiceVida y archivo BICE BiceVida.

Compara RUTs y reporta inconsistencias. Proceso especial:
- La hoja BAJAS se procesa directamente para generar archivo de eliminación
- La hoja AGREGAR se compara con la base actual para encontrar usuarios a agregar

Archivos:
- BICE Vida_users_06_02_2026.xlsx (BASE ACTUAL - todos activos e inactivos)
- 01. Enero 2026.xlsx (NUEVO - con hojas BAJAS y AGREGAR)
"""
import pandas as pd
import os
import sys
from datetime import datetime

# Agregar la carpeta padre al path para poder importar utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.comparadores import (
    normalizar_rut_comparacion,
    normalizar_ruts_dataframe,
    separar_y_guardar_resultados,
    imprimir_resumen
)
from utils.file_handlers import guardar_csv_formato_especial


def comparar_bice_vida():
    """
    Compara los RUTs entre el archivo de carga y el archivo base de BiceVida.
    Procesa las hojas BAJAS y AGREGAR de forma especial.
    """
    # Constantes para nombres de columnas
    COL_NOMBRE_ASEGURADO = 'NOMBRE ASEGURADO'
    COL_APELLIDO_PATERNO = 'APELLIDO PATERNO ASEGURADO'
    COL_APELLIDO_MATERNO = 'APELLIDO MATERNO ASEGURADO'
    COL_EMAIL = 'EMAIL'
    COL_RUT_ASEGURADO = 'RUT ASEGURADO'
    COL_DV_ASEGURADO = 'DV ASEGURADO'
    
    # Rutas de archivos
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, 'data', 'Bice Vida')
    
    # Buscar archivos dinámicamente
    archivo_base = None
    archivo_nuevo = None
    
    for filename in os.listdir(data_dir):
        # Ignorar archivos temporales de Excel
        if filename.startswith('~$'):
            continue
            
        if 'BICE Vida_users' in filename:
            archivo_base = os.path.join(data_dir, filename)
        elif filename.endswith('.xlsx') and '01.' in filename:
            archivo_nuevo = os.path.join(data_dir, filename)
    
    if not archivo_base or not archivo_nuevo:
        print("❌ Error: No se encontraron todos los archivos necesarios")
        print(f"   Base encontrado: {archivo_base is not None}")
        print(f"   Nuevo encontrado: {archivo_nuevo is not None}")
        return
    
    print("="*80)
    print("📊 COMPARACIÓN BICE VIDA - BAJAS Y AGREGAR")
    print("="*80)
    print(f"\nArchivo Base (actual): {os.path.basename(archivo_base)}")
    print(f"Archivo Nuevo (carga): {os.path.basename(archivo_nuevo)}")
    
    # Leer archivo base
    print("\n🔄 Leyendo archivos...")
    
    try:
        df_base = pd.read_excel(archivo_base)
        print("  ✓ Archivo Base leído correctamente")
    except Exception as e:
        print(f"  ❌ Error al leer archivo base: {e}")
        return
    
    # Leer archivo nuevo con sus hojas
    try:
        # Leer todas las hojas
        excel_file = pd.ExcelFile(archivo_nuevo)
        print("  ✓ Archivo Nuevo leído correctamente")
        print(f"  📄 Hojas encontradas: {', '.join(excel_file.sheet_names)}")
        
        # Buscar hojas BAJAS y AGREGAR (case insensitive)
        hoja_bajas = None
        hoja_agregar = None
        
        for sheet in excel_file.sheet_names:
            if 'baja' in sheet.lower():
                hoja_bajas = sheet
            elif 'agregar' in sheet.lower():
                hoja_agregar = sheet
        
        if not hoja_bajas or not hoja_agregar:
            print("  ⚠️  Advertencia: No se encontraron las hojas BAJAS y/o AGREGAR")
            print(f"     Hoja BAJAS: {'Encontrada' if hoja_bajas else 'No encontrada'}")
            print(f"     Hoja AGREGAR: {'Encontrada' if hoja_agregar else 'No encontrada'}")
            if not hoja_bajas and not hoja_agregar:
                return
        
        # Leer las hojas
        df_bajas = pd.read_excel(archivo_nuevo, sheet_name=hoja_bajas) if hoja_bajas else pd.DataFrame()
        df_agregar = pd.read_excel(archivo_nuevo, sheet_name=hoja_agregar) if hoja_agregar else pd.DataFrame()
        
        print(f"  ✓ Hoja BAJAS: {len(df_bajas)} registros")
        print(f"  ✓ Hoja AGREGAR: {len(df_agregar)} registros")
        
    except Exception as e:
        print(f"  ❌ Error al leer archivo nuevo: {e}")
        return
    
    print("\n📈 Registros totales:")
    print(f"  - Base (total): {len(df_base)}")
    print(f"  - Bajas: {len(df_bajas)}")
    print(f"  - Agregar: {len(df_agregar)}")
    
    # Normalizar RUTs
    print("\n🔧 Procesando RUTs...")
    
    # Normalizar RUTs en base
    df_base = normalizar_ruts_dataframe(df_base, 'RUT')
    print(f"  ✓ RUTs válidos en Base: {len(df_base)}")
    
    # Mostrar columnas de los archivos para debug
    print("\n🔍 Columnas encontradas:")
    if len(df_bajas) > 0:
        print(f"  - BAJAS: {', '.join(df_bajas.columns[:5])}...")
    if len(df_agregar) > 0:
        print(f"  - AGREGAR: {', '.join(df_agregar.columns[:5])}...")
    
    # Separar activos e inactivos en la base
    df_base_activos = df_base.copy()
    df_base_inactivos = pd.DataFrame()
    
    if 'Estado' in df_base.columns:
        df_base['Estado_str'] = df_base['Estado'].astype(str).str.upper()
        df_base_activos = df_base[df_base['Estado_str'].isin(['VERDADERO', 'TRUE', 'ACTIVO', '1'])].copy()
        df_base_inactivos = df_base[~df_base['Estado_str'].isin(['VERDADERO', 'TRUE', 'ACTIVO', '1'])].copy()
        print(f"  ✓ Base Activos: {len(df_base_activos)}")
        print(f"  ✓ Base Inactivos: {len(df_base_inactivos)}")
    
    # Procesar BAJAS
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    resultado_dir = os.path.join(script_dir, 'resultado')
    os.makedirs(resultado_dir, exist_ok=True)
    
    if len(df_bajas) > 0:
        print("\n" + "="*80)
        print("📋 PROCESANDO BAJAS")
        print("="*80)
        
        # Normalizar RUTs en bajas (columna 'rut' en minúscula)
        df_bajas = normalizar_ruts_dataframe(df_bajas, 'rut')
        print(f"  ✓ RUTs válidos en Bajas: {len(df_bajas)}")
        
        # Crear archivo de bajas en formato especial
        df_csv_bajas = pd.DataFrame({
            'RUT': df_bajas['RUT_NORM']
        })
        
        archivo_csv_bajas = os.path.join(resultado_dir, f'bajas_bice_vida_{timestamp}.csv')
        guardar_csv_formato_especial(df_csv_bajas, archivo_csv_bajas, solo_rut=True)
        print("\n💾 Archivo de BAJAS generado:")
        print(f"   📄 {os.path.basename(archivo_csv_bajas)}")
        print(f"   📊 {len(df_bajas)} RUTs a dar de baja")
    
    # Procesar AGREGAR
    if len(df_agregar) > 0:
        print("\n" + "="*80)
        print("📋 PROCESANDO AGREGAR")
        print("="*80)
        
        # Combinar RUT ASEGURADO y DV ASEGURADO en una sola columna
        df_agregar['RUT'] = df_agregar[COL_RUT_ASEGURADO].astype(str) + df_agregar[COL_DV_ASEGURADO].astype(str)
        
        # Normalizar RUTs en agregar
        df_agregar = normalizar_ruts_dataframe(df_agregar, 'RUT')
        print(f"  ✓ RUTs válidos en Agregar: {len(df_agregar)}")
        
        # Obtener sets de RUTs
        ruts_agregar = set(df_agregar['RUT_NORM'].unique())
        ruts_base_activos = set(df_base_activos['RUT_NORM'].unique())
        ruts_base_inactivos = set(df_base_inactivos['RUT_NORM'].unique())
        ruts_base_total = ruts_base_activos | ruts_base_inactivos
        
        print("\n🔢 RUTs únicos:")
        print(f"  - Agregar: {len(ruts_agregar)}")
        print(f"  - Base Total: {len(ruts_base_total)}")
        print(f"  - Base Activos: {len(ruts_base_activos)}")
        print(f"  - Base Inactivos: {len(ruts_base_inactivos)}")
        
        # Realizar comparaciones
        print("\n🔍 Realizando comparaciones...")
        
        # 1. RUTs que NO existen en la base
        no_existen = ruts_agregar - ruts_base_total
        
        # 2. RUTs que existen pero están inactivos
        existen_inactivos = ruts_agregar & ruts_base_inactivos
        
        # 3. RUTs que ya existen y están activos (no necesitan agregarse)
        ya_activos = ruts_agregar & ruts_base_activos
        
        print("\n📊 Resultados:")
        print(f"  ✅ Ya activos en base (no agregar): {len(ya_activos)}")
        print(f"  ⚠️  No existen en base (agregar): {len(no_existen)}")
        print(f"  ⚠️  Existen pero inactivos (reactivar): {len(existen_inactivos)}")
        
        # Crear DataFrame de resultados para análisis
        resultados = []
        
        # Procesar: Ya activos
        for rut in ya_activos:
            reg_agregar = df_agregar[df_agregar['RUT_NORM'] == rut].iloc[0]
            reg_base = df_base_activos[df_base_activos['RUT_NORM'] == rut].iloc[0]
            
            # Construir nombre y apellido desde las columnas del Excel
            nombre = reg_agregar.get(COL_NOMBRE_ASEGURADO, '')
            apellido_paterno = reg_agregar.get(COL_APELLIDO_PATERNO, '')
            apellido_materno = reg_agregar.get(COL_APELLIDO_MATERNO, '')
            apellido = f"{apellido_paterno} {apellido_materno}".strip()
            email = reg_agregar.get(COL_EMAIL, '')
            
            resultados.append({
                'RUT': rut,
                'ESTADO': 'YA_ACTIVO',
                'TIPO': 'BICE_VIDA',
                'NOMBRE_AGREGAR': nombre,
                'APELLIDO_AGREGAR': apellido,
                'EMAIL_AGREGAR': email,
                'NOMBRE_BASE': reg_base.get('Nombre', ''),
                'APELLIDO_BASE': reg_base.get('Apellido', ''),
                'EMAIL_BASE': reg_base.get('Email', ''),
                'OBSERVACION': 'OK - Usuario ya existe y está activo'
            })
        
        # Procesar: No existen
        for rut in no_existen:
            reg_agregar = df_agregar[df_agregar['RUT_NORM'] == rut].iloc[0]
            
            # Construir nombre y apellido desde las columnas del Excel
            nombre = reg_agregar.get(COL_NOMBRE_ASEGURADO, '')
            apellido_paterno = reg_agregar.get(COL_APELLIDO_PATERNO, '')
            apellido_materno = reg_agregar.get(COL_APELLIDO_MATERNO, '')
            apellido = f"{apellido_paterno} {apellido_materno}".strip()
            email = reg_agregar.get(COL_EMAIL, '')
            
            resultados.append({
                'RUT': rut,
                'ESTADO': 'NO_EXISTE',
                'TIPO': 'BICE_VIDA',
                'NOMBRE_AGREGAR': nombre,
                'APELLIDO_AGREGAR': apellido,
                'EMAIL_AGREGAR': email,
                'NOMBRE_BASE': '',
                'APELLIDO_BASE': '',
                'EMAIL_BASE': '',
                'OBSERVACION': 'AGREGAR - Usuario no existe en base'
            })
        
        # Procesar: Existen pero inactivos
        for rut in existen_inactivos:
            reg_agregar = df_agregar[df_agregar['RUT_NORM'] == rut].iloc[0]
            reg_base = df_base_inactivos[df_base_inactivos['RUT_NORM'] == rut].iloc[0]
            
            # Construir nombre y apellido desde las columnas del Excel
            nombre = reg_agregar.get(COL_NOMBRE_ASEGURADO, '')
            apellido_paterno = reg_agregar.get(COL_APELLIDO_PATERNO, '')
            apellido_materno = reg_agregar.get(COL_APELLIDO_MATERNO, '')
            apellido = f"{apellido_paterno} {apellido_materno}".strip()
            email = reg_agregar.get(COL_EMAIL, '')
            
            resultados.append({
                'RUT': rut,
                'ESTADO': 'INACTIVO',
                'TIPO': 'BICE_VIDA',
                'NOMBRE_AGREGAR': nombre,
                'APELLIDO_AGREGAR': apellido,
                'EMAIL_AGREGAR': email,
                'NOMBRE_BASE': reg_base.get('Nombre', ''),
                'APELLIDO_BASE': reg_base.get('Apellido', ''),
                'EMAIL_BASE': reg_base.get('Email', ''),
                'OBSERVACION': 'REACTIVAR - Usuario existe pero está inactivo'
            })
        
        # Crear DataFrame de resultados
        df_resultados = pd.DataFrame(resultados)
        
        # Orden de estados
        orden_estados = {
            'YA_ACTIVO': 1,
            'NO_EXISTE': 2,
            'INACTIVO': 3
        }
        
        # Separar y guardar usando función común
        df_coincidencias, df_inconsistencias, archivos = separar_y_guardar_resultados(
            df_resultados, script_dir, timestamp, orden_estados, prefijo='bice_vida_'
        )
        
        # Imprimir resumen
        imprimir_resumen(df_coincidencias, df_inconsistencias, archivos)
        
        # Generar CSV especial para AGREGAR (no existen + inactivos)
        df_para_agregar = df_inconsistencias[
            df_inconsistencias['ESTADO'].isin(['NO_EXISTE', 'INACTIVO'])
        ].copy()
        
        if len(df_para_agregar) > 0:
            # Preparar DataFrame con el formato requerido
            df_csv_agregar = pd.DataFrame({
                'Nombre': df_para_agregar['NOMBRE_AGREGAR'],
                'Apellido': df_para_agregar['APELLIDO_AGREGAR'],
                'Email': df_para_agregar['EMAIL_AGREGAR'],
                'RUT': df_para_agregar['RUT']
            })
            
            # Guardar en formato especial
            archivo_csv_agregar = os.path.join(resultado_dir, f'agregar_bice_vida_{timestamp}.csv')
            guardar_csv_formato_especial(df_csv_agregar, archivo_csv_agregar)
            print(f"   📄 Usuarios a AGREGAR/REACTIVAR: {os.path.basename(archivo_csv_agregar)}")
            print(f"      - No existen: {len(df_para_agregar[df_para_agregar['ESTADO'] == 'NO_EXISTE'])}")
            print(f"      - Inactivos: {len(df_para_agregar[df_para_agregar['ESTADO'] == 'INACTIVO'])}")
        
        # Mostrar muestras
        if len(df_inconsistencias) > 0:
            print("\n🔍 Muestra de usuarios a procesar (primeros 10):")
            columnas_mostrar = ['RUT', 'ESTADO', 'NOMBRE_AGREGAR', 'EMAIL_AGREGAR', 'OBSERVACION']
            print(df_inconsistencias.head(10)[columnas_mostrar].to_string(index=False))
    
    print("\n" + "="*80)
    print("✅ Proceso completado")
    print("="*80)


if __name__ == "__main__":
    comparar_bice_vida()
