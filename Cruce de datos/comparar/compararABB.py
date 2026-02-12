"""
Script para procesar datos de ABB:

Proceso especial:
- Las hojas BAJAS ABB y BAJAS EXTERNOS se procesan directamente para generar archivo de desactivación
- La hoja ALTAS ABB se compara con la base actual para encontrar usuarios a agregar (activación)

Archivos esperados en carpeta `data/ABB`:
- [fecha]_Bajas_Altas Seguro de Mascotas.xlsx (MOVIMIENTOS - con hojas BAJAS ABB, BAJAS EXTERNOS y ALTAS ABB)
- ABB_users_[fecha].xlsx (BASE ACTUAL - usuarios existentes)
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


def normalizar_ruts_dataframe_abb(df, col_rut, col_dv=None):
    """
    Normaliza RUTs en un DataFrame para comparación ABB.
    Si tiene columna de DV separada, las combina primero.
    """
    if col_dv and col_dv in df.columns:
        # Combinar RUT + DV
        df['RUT_COMPLETO'] = df[col_rut].astype(str).str.strip() + '-' + df[col_dv].astype(str).str.strip()
        col_a_normalizar = 'RUT_COMPLETO'
    else:
        col_a_normalizar = col_rut
    
    # Normalizar RUTs
    df['RUT_NORM'] = df[col_a_normalizar].apply(normalizar_rut_comparacion)
    
    # Filtrar solo RUTs válidos
    df = df[df['RUT_NORM'].notna() & (df['RUT_NORM'] != '')].copy()
    
    # Crear columna RUT limpia para mostrar
    df['RUT'] = df['RUT_NORM']
    
    return df


def procesar_abb():
    """
    Procesa los datos de ABB:
    - BAJAS ABB y BAJAS EXTERNOS: genera archivos de desactivación directamente
    - ALTAS ABB: compara con base actual y genera archivo de activación
    """
    # Rutas de archivos
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, 'data', 'ABB')
    
    # Buscar archivos dinámicamente
    archivo_movimientos = None
    archivo_base = None
    
    if not os.path.exists(data_dir):
        print(f"❌ Error: no existe la carpeta de datos: {data_dir}")
        return
    
    for filename in os.listdir(data_dir):
        # Ignorar archivos temporales de Excel
        if filename.startswith('~$'):
            continue
            
        if 'Bajas_Altas Seguro de Mascotas' in filename:
            archivo_movimientos = os.path.join(data_dir, filename)
        elif 'ABB_users' in filename:
            archivo_base = os.path.join(data_dir, filename)
    
    if not archivo_movimientos or not archivo_base:
        print("❌ Error: No se encontraron todos los archivos necesarios")
        print(f"   Movimientos encontrado: {archivo_movimientos is not None}")
        print(f"   Base ABB encontrado: {archivo_base is not None}")
        return
    
    print("="*80)
    print("📊 PROCESAMIENTO ABB - BAJAS Y ALTAS")
    print("="*80)
    print(f"\nArchivo Movimientos: {os.path.basename(archivo_movimientos)}")
    print(f"Archivo Base ABB: {os.path.basename(archivo_base)}")
    
    # Crear carpeta de resultado
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    resultado_dir = os.path.join(script_dir, 'resultado')
    os.makedirs(resultado_dir, exist_ok=True)
    
    # Leer archivo de movimientos (con múltiples hojas)
    print("\n🔄 Leyendo archivo de movimientos...")
    
    try:
        # Leer todas las hojas
        hojas_movimientos = pd.read_excel(archivo_movimientos, sheet_name=None)
        print(f"  ✓ Hojas encontradas: {list(hojas_movimientos.keys())}")
    except Exception as e:
        print(f"  ❌ Error al leer archivo de movimientos: {e}")
        return
    
    # Leer archivo base ABB
    print("\n🔄 Leyendo archivo base ABB...")
    try:
        df_base_abb = pd.read_excel(archivo_base)
        print(f"  ✓ Archivo base ABB leído correctamente ({len(df_base_abb)} registros)")
    except Exception as e:
        print(f"  ❌ Error al leer archivo base ABB: {e}")
        return
    
    # Filtrar solo registros activos en base ABB
    if 'Estado' in df_base_abb.columns:
        df_base_abb = filtrar_activos(df_base_abb, 'Estado')
        print(f"  ✓ Registros activos en base ABB: {len(df_base_abb)}")
    
    # Normalizar RUTs en base ABB
    df_base_abb = normalizar_ruts_dataframe(df_base_abb, 'RUT')
    ruts_base_abb = set(df_base_abb['RUT_NORM'].unique())
    print(f"  ✓ RUTs únicos en base ABB: {len(ruts_base_abb)}")
    
    # ========================================
    # PROCESAR BAJAS ABB Y BAJAS EXTERNOS
    # ========================================
    print("\n" + "="*60)
    print("📋 PROCESANDO BAJAS")
    print("="*60)
    
    hojas_bajas = ['Bajas ABB', 'Bajas EXTERNOS', 'BAJAS ABB', 'BAJAS EXTERNOS', 'Bajas Externos', 'EXTERNOS', 'Externos']
    df_bajas_total = pd.DataFrame()
    
    for hoja_nombre in hojas_bajas:
        if hoja_nombre in hojas_movimientos:
            df_hoja = hojas_movimientos[hoja_nombre]
            if not df_hoja.empty:
                print(f"\n🔍 Procesando hoja '{hoja_nombre}': {len(df_hoja)} registros")
                
                # Intentar normalizar RUTs (buscar columnas posibles)
                columnas_rut = ['RUT', 'Rut', 'rut', 'RUT Usuario', 'RUT_USUARIO']
                columna_rut_encontrada = None
                
                for col in columnas_rut:
                    if col in df_hoja.columns:
                        columna_rut_encontrada = col
                        break
                
                if columna_rut_encontrada:
                    try:
                        df_hoja = normalizar_ruts_dataframe(df_hoja, columna_rut_encontrada)
                        df_bajas_total = pd.concat([df_bajas_total, df_hoja], ignore_index=True)
                        print(f"  ✓ RUTs válidos procesados: {len(df_hoja)}")
                    except Exception as e:
                        print(f"  ⚠️  Error procesando RUTs en {hoja_nombre}: {e}")
                else:
                    print(f"  ⚠️  No se encontró columna de RUT en {hoja_nombre}")
    
    # Generar archivo de bajas (desactivación)
    if len(df_bajas_total) > 0:
        df_bajas_total = df_bajas_total.drop_duplicates(subset=['RUT_NORM']).copy()
        archivo_bajas = os.path.join(resultado_dir, f'bajas_abb_desactivacion_{timestamp}.csv')
        
        df_csv_bajas = pd.DataFrame({
            'RUT': df_bajas_total['RUT_NORM']
        })
        
        guardar_csv_formato_especial(df_csv_bajas, archivo_bajas, solo_rut=True)
        print(f"\n💾 Archivo de BAJAS (desactivación) generado:")
        print(f"   📄 {os.path.basename(archivo_bajas)} ({len(df_bajas_total)} RUTs únicos)")
    else:
        print("\n⚠️  No se encontraron registros de bajas para procesar")
    
    # ========================================
    # PROCESAR ALTAS ABB
    # ========================================
    print("\n" + "="*60)
    print("📋 PROCESANDO ALTAS ABB")
    print("="*60)
    
    hojas_altas = ['Altas ABB', 'ALTAS ABB']
    df_altas = None
    
    for hoja_nombre in hojas_altas:
        if hoja_nombre in hojas_movimientos:
            df_altas = hojas_movimientos[hoja_nombre]
            if not df_altas.empty:
                print(f"\n🔍 Procesando hoja '{hoja_nombre}': {len(df_altas)} registros")
                break
    
    if df_altas is None or df_altas.empty:
        print("\n⚠️  No se encontró hoja de Altas ABB o está vacía")
        print("\n" + "="*80)
        print("✅ Proceso completado")
        print("="*80)
        return
    
    # Intentar normalizar RUTs en altas
    columnas_rut = ['RUT', 'Rut', 'rut', 'RUT Usuario', 'RUT_USUARIO']
    columnas_dv = ['DV', 'Dv', 'dv', 'DV Usuario', 'DV_USUARIO']
    
    columna_rut_encontrada = None
    columna_dv_encontrada = None
    
    for col in columnas_rut:
        if col in df_altas.columns:
            columna_rut_encontrada = col
            break
    
    for col in columnas_dv:
        if col in df_altas.columns:
            columna_dv_encontrada = col
            break
    
    if not columna_rut_encontrada:
        print("  ❌ No se encontró columna de RUT en Altas ABB")
        return
    
    try:
        df_altas = normalizar_ruts_dataframe_abb(df_altas, columna_rut_encontrada, columna_dv_encontrada)
        print(f"  ✓ RUTs válidos en Altas: {len(df_altas)}")
    except Exception as e:
        print(f"  ❌ Error procesando RUTs en Altas: {e}")
        return
    
    # Comparar con base ABB para encontrar nuevos usuarios
    ruts_altas = set(df_altas['RUT_NORM'].unique())
    print(f"  ✓ RUTs únicos en Altas: {len(ruts_altas)}")
    
    # RUTs que están en Altas pero NO en base ABB (hay que agregar)
    ruts_nuevos = ruts_altas - ruts_base_abb
    ruts_ya_existen = ruts_altas & ruts_base_abb
    
    print(f"\n📊 RESULTADOS:")
    print(f"  ✅ RUTs nuevos a agregar: {len(ruts_nuevos)}")
    print(f"  ⚠️  RUTs que ya existen: {len(ruts_ya_existen)}")
    
    # Buscar columnas de datos personales según el mapeo correcto (definir una vez para ambos casos)
    columnas_nombre = ['Nombre', 'NOMBRE', 'nombre']
    columnas_apellido_pat = ['Apellido Pat.', 'Apellido Pat', 'APELLIDO_PAT', 'ApellidoPat', 'Apellido Paterno']
    columnas_apellido_mat = ['Apellido Mat.', 'Apellido Mat', 'APELLIDO_MAT', 'ApellidoMat', 'Apellido Materno']
    columnas_email = ['Mail', 'MAIL', 'mail', 'Email', 'EMAIL', 'email']
    
    def encontrar_columna(df, opciones):
        for col in opciones:
            if col in df.columns:
                return col
        return None
    
    col_nombre = encontrar_columna(df_altas, columnas_nombre)
    col_apellido_pat = encontrar_columna(df_altas, columnas_apellido_pat)
    col_apellido_mat = encontrar_columna(df_altas, columnas_apellido_mat)
    col_email = encontrar_columna(df_altas, columnas_email)

    # Generar archivo de altas (activación) solo para usuarios nuevos
    if len(ruts_nuevos) > 0:
        df_altas_nuevos = df_altas[df_altas['RUT_NORM'].isin(ruts_nuevos)].copy()
        
        # Combinar apellido paterno y materno
        apellido_completo = ''
        if col_apellido_pat and col_apellido_mat:
            apellido_completo = (df_altas_nuevos[col_apellido_pat].fillna('').astype(str) + ' ' + 
                               df_altas_nuevos[col_apellido_mat].fillna('').astype(str)).str.strip()
        elif col_apellido_pat:
            apellido_completo = df_altas_nuevos[col_apellido_pat].fillna('')
        elif col_apellido_mat:
            apellido_completo = df_altas_nuevos[col_apellido_mat].fillna('')
        
        df_csv_altas = pd.DataFrame({
            'Nombre': df_altas_nuevos[col_nombre].fillna('') if col_nombre else '',
            'Apellido': apellido_completo,
            'Email': df_altas_nuevos[col_email].fillna('') if col_email else '',
            'Rut': df_altas_nuevos['RUT_NORM']  # Usar 'Rut' según especificación del usuario
        })
        
        archivo_altas = os.path.join(resultado_dir, f'altas_abb_activacion_{timestamp}.csv')
        guardar_csv_formato_especial(df_csv_altas, archivo_altas, columnas=['Nombre', 'Apellido', 'Email', 'Rut'])
        print(f"\n💾 Archivo de ALTAS (activación) generado:")
        print(f"   📄 {os.path.basename(archivo_altas)} ({len(ruts_nuevos)} usuarios nuevos)")
        
        # Imprimir muestra
        print(f"\n🔍 Muestra de usuarios a agregar (primeros 5):")
        print(df_csv_altas.head().to_string(index=False))
    else:
        print("\n✅ No hay usuarios nuevos para agregar (todos ya existen en la base)")
    
    # Generar resumen de usuarios que ya existen
    if len(ruts_ya_existen) > 0:
        df_ya_existen = df_altas[df_altas['RUT_NORM'].isin(ruts_ya_existen)].copy()
        archivo_ya_existen = os.path.join(resultado_dir, f'altas_abb_ya_existen_{timestamp}.xlsx')
        
        # Combinar apellidos para el resumen también
        apellido_completo_existentes = ''
        if col_apellido_pat and col_apellido_mat:
            apellido_completo_existentes = (df_ya_existen[col_apellido_pat].fillna('').astype(str) + ' ' + 
                                          df_ya_existen[col_apellido_mat].fillna('').astype(str)).str.strip()
        elif col_apellido_pat:
            apellido_completo_existentes = df_ya_existen[col_apellido_pat].fillna('')
        elif col_apellido_mat:
            apellido_completo_existentes = df_ya_existen[col_apellido_mat].fillna('')
        
        # Preparar DataFrame informativo
        df_resumen_existen = pd.DataFrame({
            'Rut': df_ya_existen['RUT_NORM'],
            'NOMBRE_ALTA': df_ya_existen[col_nombre].fillna('') if col_nombre else '',
            'APELLIDO_COMPLETO': apellido_completo_existentes,
            'EMAIL_ALTA': df_ya_existen[col_email].fillna('') if col_email else '',
            'OBSERVACION': 'Usuario ya existe en base ABB'
        })
        
        df_resumen_existen.to_excel(archivo_ya_existen, index=False)
        print(f"\n💾 Archivo de referencia (usuarios que ya existen):")
        print(f"   📄 {os.path.basename(archivo_ya_existen)}")
    
    print("\n" + "="*80)
    print("✅ Proceso completado")
    print("="*80)


if __name__ == "__main__":
    procesar_abb()