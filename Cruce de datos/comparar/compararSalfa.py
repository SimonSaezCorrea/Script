"""
Script para comparar datos entre archivo de carga Salfa y archivo Salfa_users.

Procesa el archivo "Movimiento FEBRERO 2026" que contiene 3 hojas:
- Seguros Pawer (IGNORADA)
- Bajas Salfa Febrero (genera listado de RUTs a dar de baja)
- Ingresos Salfa Febrero (genera listado de altas, validando que no existan en Salfa_users)

Archivos:
- Movimiento FEBRERO 2026 - PAWER.xlsx (CARGA - con hojas Bajas e Ingresos)
- Salfa_users_XX_XX_XXXX.xlsx (BASE ACTUAL)
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
    imprimir_resumen
)
from utils.file_handlers import guardar_csv_formato_especial


def comparar_salfa():
    """
    Compara los RUTs entre el archivo de movimientos de Salfa y el archivo base.
    Procesa las hojas Bajas e Ingresos de forma especial.
    """
    # Rutas de archivos
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, 'data', 'Salfa')
    
    # Buscar archivos dinámicamente
    archivo_movimientos = None
    archivo_base = None
    
    for filename in os.listdir(data_dir):
        # Ignorar archivos temporales de Excel
        if filename.startswith('~$'):
            continue
            
        if 'Movimiento FEBRERO 2026' in filename:
            archivo_movimientos = os.path.join(data_dir, filename)
        elif 'Salfa_users' in filename:
            archivo_base = os.path.join(data_dir, filename)
    
    if not archivo_movimientos or not archivo_base:
        print("❌ Error: No se encontraron todos los archivos necesarios")
        print(f"   Movimientos encontrado: {archivo_movimientos is not None}")
        print(f"   Base encontrado: {archivo_base is not None}")
        return
    
    print("="*80)
    print("📊 COMPARACIÓN SALFA - BAJAS E INGRESOS")
    print("="*80)
    print(f"\nArchivo Movimientos: {os.path.basename(archivo_movimientos)}")
    print(f"Archivo Base (actual): {os.path.basename(archivo_base)}")
    
    # Leer archivo base
    print("\n🔄 Leyendo archivos...")
    
    try:
        df_base = pd.read_excel(archivo_base)
        print("  ✓ Archivo Base leído correctamente")
    except Exception as e:
        print(f"  ❌ Error al leer archivo base: {e}")
        return
    
    # Leer archivo de movimientos con sus hojas
    try:
        # Leer todas las hojas
        excel_file = pd.ExcelFile(archivo_movimientos)
        print("  ✓ Archivo Movimientos leído correctamente")
        print(f"  📄 Hojas encontradas: {', '.join(excel_file.sheet_names)}")
        
        # Buscar hojas Bajas e Ingresos (case insensitive)
        hoja_bajas = None
        hoja_ingresos = None
        
        for sheet in excel_file.sheet_names:
            if 'baja' in sheet.lower() and 'salfa' in sheet.lower():
                hoja_bajas = sheet
            elif 'ingreso' in sheet.lower() and 'salfa' in sheet.lower():
                hoja_ingresos = sheet
        
        if not hoja_bajas or not hoja_ingresos:
            print("  ⚠️  Advertencia: No se encontraron las hojas de Bajas y/o Ingresos")
            print(f"     Hoja BAJAS: {'Encontrada' if hoja_bajas else 'No encontrada'}")
            print(f"     Hoja INGRESOS: {'Encontrada' if hoja_ingresos else 'No encontrada'}")
            if not hoja_bajas and not hoja_ingresos:
                return
        
        # Leer las hojas
        df_bajas = pd.read_excel(archivo_movimientos, sheet_name=hoja_bajas) if hoja_bajas else pd.DataFrame()
        df_ingresos = pd.read_excel(archivo_movimientos, sheet_name=hoja_ingresos) if hoja_ingresos else pd.DataFrame()
        
        print(f"  ✓ Hoja BAJAS: {len(df_bajas)} registros")
        print(f"  ✓ Hoja INGRESOS: {len(df_ingresos)} registros")
        
    except Exception as e:
        print(f"  ❌ Error al leer archivo de movimientos: {e}")
        return
    
    print("\n📈 Registros totales:")
    print(f"  - Base (total): {len(df_base)}")
    print(f"  - Bajas: {len(df_bajas)}")
    print(f"  - Ingresos: {len(df_ingresos)}")
    
    # Normalizar RUTs en base
    print("\n🔧 Procesando RUTs...")
    df_base = normalizar_ruts_dataframe(df_base, 'RUT')
    print(f"  ✓ RUTs válidos en Base: {len(df_base)}")
    
    # Mostrar columnas de los archivos para debug
    print("\n🔍 Columnas encontradas:")
    if len(df_bajas) > 0:
        print(f"  - BAJAS: {', '.join(df_bajas.columns[:5])}...")
    if len(df_ingresos) > 0:
        print(f"  - INGRESOS: {', '.join(df_ingresos.columns[:5])}...")
    
    # Separar activos e inactivos en la base
    df_base_activos = df_base.copy()
    df_base_inactivos = pd.DataFrame()
    
    if 'Estado' in df_base.columns:
        df_base['Estado_str'] = df_base['Estado'].astype(str).str.upper()
        df_base_activos = df_base[df_base['Estado_str'].isin(['VERDADERO', 'TRUE', 'ACTIVO', '1'])].copy()
        df_base_inactivos = df_base[~df_base['Estado_str'].isin(['VERDADERO', 'TRUE', 'ACTIVO', '1'])].copy()
        print(f"\n  ✓ Base Activos: {len(df_base_activos)}")
        print(f"  ✓ Base Inactivos: {len(df_base_inactivos)}")
    
    # Crear directorio de resultados
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    resultado_dir = os.path.join(script_dir, 'resultado')
    os.makedirs(resultado_dir, exist_ok=True)
    
    # Procesar BAJAS
    if len(df_bajas) > 0:
        print("\n" + "="*80)
        print("📋 PROCESANDO BAJAS")
        print("="*80)
        
        # Detectar columna de RUT (puede ser 'RUT', 'Rut', 'rut', etc.)
        col_rut_bajas = None
        for col in df_bajas.columns:
            if col.lower().strip() == 'rut':
                col_rut_bajas = col
                break
        
        if not col_rut_bajas:
            print("  ❌ Error: No se encontró columna 'RUT' en la hoja de Bajas")
        else:
            # Normalizar RUTs en bajas
            df_bajas = normalizar_ruts_dataframe(df_bajas, col_rut_bajas)
            print(f"  ✓ RUTs válidos en Bajas: {len(df_bajas)}")
            
            # Crear archivo de bajas en formato especial
            df_csv_bajas = pd.DataFrame({
                'RUT': df_bajas['RUT_NORM']
            })
            
            archivo_csv_bajas = os.path.join(resultado_dir, f'salfa_bajas_{timestamp}.csv')
            guardar_csv_formato_especial(df_csv_bajas, archivo_csv_bajas, solo_rut=True)
            print("\n💾 Archivo de BAJAS generado:")
            print(f"   📄 {os.path.basename(archivo_csv_bajas)}")
            print(f"   📊 {len(df_bajas)} RUTs a dar de baja")
    
    # Procesar INGRESOS
    if len(df_ingresos) > 0:
        print("\n" + "="*80)
        print("📋 PROCESANDO INGRESOS")
        print("="*80)
        
        # Detectar columnas necesarias
        columnas_mapeadas = {}
        
        for col in df_ingresos.columns:
            col_lower = col.lower().strip()
            # Buscar columna de nombre completo primero
            if 'nombre completo' in col_lower:
                columnas_mapeadas['nombre_completo'] = col
            elif 'nombre' in col_lower and 'apellido' not in col_lower and 'completo' not in col_lower:
                if 'nombre' not in columnas_mapeadas:
                    columnas_mapeadas['nombre'] = col
            elif 'apellido' in col_lower:
                if 'apellido' not in columnas_mapeadas:
                    columnas_mapeadas['apellido'] = col
                # Si hay apellido paterno y materno, concatenarlos
                elif 'paterno' in col_lower or 'materno' in col_lower:
                    if 'apellidos' not in columnas_mapeadas:
                        columnas_mapeadas['apellidos'] = [columnas_mapeadas['apellido']]
                    columnas_mapeadas['apellidos'].append(col)
            elif 'email' in col_lower or 'correo' in col_lower or 'mail' in col_lower:
                columnas_mapeadas['email'] = col
            elif col_lower == 'rut':
                columnas_mapeadas['rut'] = col
        
        print(f"\n  📋 Columnas detectadas:")
        for key, value in columnas_mapeadas.items():
            print(f"     - {key}: {value}")
        
        # Verificar que tenemos todas las columnas necesarias
        columnas_requeridas = ['rut', 'email']
        # Nombre puede estar en 'nombre_completo' o separado
        if 'nombre_completo' not in columnas_mapeadas and 'nombre' not in columnas_mapeadas:
            columnas_requeridas.append('nombre/nombre_completo')
        
        faltantes = [col for col in columnas_requeridas if col not in columnas_mapeadas]
        
        if faltantes:
            print(f"\n  ❌ Error: Faltan columnas necesarias: {', '.join(faltantes)}")
        else:
            # Preparar DataFrame con columnas unificadas
            df_proc = pd.DataFrame()
            
            # Manejar nombre completo o nombre/apellido separados
            if 'nombre_completo' in columnas_mapeadas:
                # Dividir Nombre Completo en Nombre y Apellido
                # Asumimos que el primer término es el nombre y el resto apellidos
                nombres_completos = df_ingresos[columnas_mapeadas['nombre_completo']].astype(str)
                
                df_proc['Nombre'] = nombres_completos.apply(
                    lambda x: x.split()[0] if isinstance(x, str) and x.strip() else ''
                )
                df_proc['Apellido'] = nombres_completos.apply(
                    lambda x: ' '.join(x.split()[1:]) if isinstance(x, str) and len(x.split()) > 1 else ''
                )
            else:
                # Usar columnas separadas
                if 'nombre' in columnas_mapeadas:
                    df_proc['Nombre'] = df_ingresos[columnas_mapeadas['nombre']]
                else:
                    df_proc['Nombre'] = ''
                
                # Manejar apellidos
                if 'apellidos' in columnas_mapeadas:
                    # Concatenar todos los apellidos
                    apellidos_cols = columnas_mapeadas['apellidos']
                    df_proc['Apellido'] = df_ingresos[apellidos_cols].apply(
                        lambda row: ' '.join(str(val).strip() for val in row if pd.notna(val) and str(val).strip()),
                        axis=1
                    )
                elif 'apellido' in columnas_mapeadas:
                    df_proc['Apellido'] = df_ingresos[columnas_mapeadas['apellido']]
                else:
                    df_proc['Apellido'] = ''
            
            # Agregar email y rut
            df_proc['Email'] = df_ingresos[columnas_mapeadas['email']]
            df_proc['RUT'] = df_ingresos[columnas_mapeadas['rut']]
            
            # Normalizar RUTs en ingresos
            df_proc = normalizar_ruts_dataframe(df_proc, 'RUT')
            print(f"\n  ✓ RUTs válidos en Ingresos: {len(df_proc)}")
            
            # Obtener sets de RUTs
            ruts_ingresos = set(df_proc['RUT_NORM'].unique())
            ruts_base_activos = set(df_base_activos['RUT_NORM'].unique())
            ruts_base_inactivos = set(df_base_inactivos['RUT_NORM'].unique())
            ruts_base_total = ruts_base_activos | ruts_base_inactivos
            
            print("\n🔢 RUTs únicos:")
            print(f"  - Ingresos: {len(ruts_ingresos)}")
            print(f"  - Base Total: {len(ruts_base_total)}")
            print(f"  - Base Activos: {len(ruts_base_activos)}")
            print(f"  - Base Inactivos: {len(ruts_base_inactivos)}")
            
            # Realizar comparaciones
            print("\n🔍 Realizando comparaciones...")
            
            # 1. RUTs que NO existen en la base
            no_existen = ruts_ingresos - ruts_base_total
            
            # 2. RUTs que existen pero están inactivos
            existen_inactivos = ruts_ingresos & ruts_base_inactivos
            
            # 3. RUTs que ya existen y están activos (no necesitan agregarse)
            ya_activos = ruts_ingresos & ruts_base_activos
            
            print("\n📊 Resultados:")
            print(f"  ✅ Ya activos en base (no agregar): {len(ya_activos)}")
            print(f"  ⚠️  No existen en base (agregar): {len(no_existen)}")
            print(f"  ⚠️  Existen pero inactivos (reactivar): {len(existen_inactivos)}")
            
            # Filtrar solo los que NO existen o están inactivos
            ruts_a_agregar = no_existen | existen_inactivos
            df_ingresos_filtrado = df_proc[df_proc['RUT_NORM'].isin(ruts_a_agregar)].copy()
            
            # Agregar columna de estado para análisis
            df_ingresos_filtrado['ESTADO'] = df_ingresos_filtrado['RUT_NORM'].apply(
                lambda rut: 'NUEVO' if rut in no_existen else 'REACTIVAR'
            )
            
            # Crear archivo de ingresos en formato especial
            df_csv_ingresos = df_ingresos_filtrado[['Nombre', 'Apellido', 'Email', 'RUT_NORM']].copy()
            df_csv_ingresos.columns = ['Nombre', 'Apellido', 'Email', 'RUT']
            
            archivo_csv_ingresos = os.path.join(resultado_dir, f'salfa_ingresos_{timestamp}.csv')
            guardar_csv_formato_especial(df_csv_ingresos, archivo_csv_ingresos, 
                                        columnas=['Nombre', 'Apellido', 'Email', 'RUT'])
            
            print("\n💾 Archivo de INGRESOS generado:")
            print(f"   📄 {os.path.basename(archivo_csv_ingresos)}")
            print(f"   📊 {len(df_ingresos_filtrado)} registros a agregar")
            print(f"       - Nuevos: {len(no_existen)}")
            print(f"       - Reactivar: {len(existen_inactivos)}")
            
            # Guardar archivo Excel con análisis completo
            archivo_excel_analisis = os.path.join(resultado_dir, f'salfa_analisis_ingresos_{timestamp}.xlsx')
            df_ingresos_filtrado.to_excel(archivo_excel_analisis, index=False, engine='openpyxl')
            print(f"\n📊 Archivo de análisis completo:")
            print(f"   📄 {os.path.basename(archivo_excel_analisis)}")
            
            # Si hay usuarios ya activos, mostrar algunos ejemplos
            if len(ya_activos) > 0:
                print(f"\n⚠️  {len(ya_activos)} usuarios ya están activos en la base:")
                df_ya_activos = df_proc[df_proc['RUT_NORM'].isin(ya_activos)].head(5)
                for _, row in df_ya_activos.iterrows():
                    print(f"     - {row['Nombre']} {row['Apellido']} ({row['RUT_NORM']})")
                if len(ya_activos) > 5:
                    print(f"     ... y {len(ya_activos) - 5} más")
    
    print("\n" + "="*80)
    print("✅ PROCESO COMPLETADO")
    print("="*80)
    print(f"\n📁 Archivos generados en: {resultado_dir}")


if __name__ == "__main__":
    comparar_salfa()
