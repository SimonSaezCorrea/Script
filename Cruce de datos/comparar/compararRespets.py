"""
Script para comparar datos entre archivo Base Asegurados ResPets y ResPets_users.

Proceso:
1. ALTAS: Extrae usuarios de la hoja "Activos" que NO existen en ResPets_users
   - Maneja duplicados agregando -copy al email y 0 al final del RUT
2. BAJAS (no en BASE): Detecta usuarios activos en ResPets_users que NO están en Base Activos
3. BAJAS (en Inactivos): Extrae usuarios de la hoja "Inactivos" que están activos en ResPets_users
   - Verifica columna "Estado" (VERDADERO/FALSO)

Archivos esperados en carpeta `data/Respets`:
- Base Asegurados ResPets.xlsx (con hojas: Activos, Inactivos)
- ResPets_users_[fecha].xlsx (base actual)
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
    separar_y_guardar_resultados,
    imprimir_resumen
)
from utils.file_handlers import guardar_csv_formato_especial


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


def comparar_respets():
    """
    Compara los datos entre Base Asegurados ResPets y ResPets_users.
    """
    # Rutas de archivos
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, 'data', 'Respets')
    
    # Buscar archivos dinámicamente
    archivo_base = None
    archivo_users = None
    
    if not os.path.exists(data_dir):
        print(f"❌ Error: no existe la carpeta de datos: {data_dir}")
        return
    
    for filename in os.listdir(data_dir):
        # Ignorar archivos temporales de Excel
        if filename.startswith('~$'):
            continue
            
        if 'Base Asegurados ResPets' in filename:
            archivo_base = os.path.join(data_dir, filename)
        elif 'ResPets_users' in filename:
            archivo_users = os.path.join(data_dir, filename)
    
    if not archivo_base or not archivo_users:
        print("❌ Error: No se encontraron todos los archivos necesarios")
        print(f"   Base encontrada: {archivo_base is not None}")
        print(f"   ResPets_users encontrado: {archivo_users is not None}")
        return
    
    print("="*80)
    print("📊 COMPARACIÓN BASE vs RESPETS_USERS")
    print("="*80)
    print(f"\nArchivo Base: {os.path.basename(archivo_base)}")
    print(f"Archivo ResPets_users: {os.path.basename(archivo_users)}")
    
    # Crear carpeta de resultado
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    resultado_dir = os.path.join(script_dir, 'resultado')
    os.makedirs(resultado_dir, exist_ok=True)
    
    # Leer archivos
    print("\n🔄 Leyendo archivos...")
    
    try:
        # Leer hoja de Activos (header en fila 0)
        df_activos = pd.read_excel(archivo_base, sheet_name='Activos', header=0)
        print(f"  ✓ Hoja Activos leída correctamente ({len(df_activos)} registros)")
    except Exception as e:
        print(f"  ❌ Error al leer hoja Activos: {e}")
        return
    
    try:
        # Leer hoja de Inactivos (header en fila 1)
        df_inactivos = pd.read_excel(archivo_base, sheet_name='Inactivos', header=1)
        print(f"  ✓ Hoja Inactivos leída correctamente ({len(df_inactivos)} registros)")
    except Exception as e:
        print(f"  ❌ Error al leer hoja Inactivos: {e}")
        return
    
    try:
        df_users = pd.read_excel(archivo_users)
        print(f"  ✓ Archivo ResPets_users leído correctamente ({len(df_users)} registros)")
    except Exception as e:
        print(f"  ❌ Error al leer archivo ResPets_users: {e}")
        return
    
    # Normalizar RUTs en df_users
    if 'RUT' in df_users.columns:
        df_users['RUT_NORM'] = df_users['RUT'].apply(normalizar_rut_comparacion)
    
    # ========================================
    # PASO 1: PROCESAR ALTAS (Activos que no están en ResPets_users)
    # ========================================
    print("\n" + "="*80)
    print("📋 PASO 1: PROCESANDO ALTAS (usuarios a agregar)")
    print("="*80)
    
    # Verificar columnas necesarias en Activos
    if 'rut_pagador' not in df_activos.columns:
        print("  ❌ No se encontró columna 'rut_pagador' en Activos")
        return
    
    # Verificar columnas necesarias en ResPets_users
    if 'RUT' not in df_users.columns or 'Estado' not in df_users.columns:
        print("  ❌ No se encontró columna 'RUT' o 'Estado' en ResPets_users")
        return
    
    # Filtrar solo usuarios activos en ResPets_users
    df_users_activos = df_users[df_users['Estado'] == True].copy()
    print(f"\n  🔍 Usuarios activos en ResPets_users: {len(df_users_activos)} de {len(df_users)}")
    
    # Normalizar RUTs en Activos
    df_activos['RUT_NORM'] = df_activos['rut_pagador'].apply(normalizar_rut_comparacion)
    df_activos = df_activos[df_activos['RUT_NORM'] != ''].copy()
    print(f"  ✓ Registros válidos en Activos: {len(df_activos)}")
    
    # Normalizar RUTs en ResPets_users
    df_users_activos['RUT_NORM'] = df_users_activos['RUT'].apply(normalizar_rut_comparacion)
    df_users_activos = df_users_activos[df_users_activos['RUT_NORM'] != ''].copy()
    
    # Obtener set de RUTs que existen en ResPets_users (activos)
    ruts_users = set(df_users_activos['RUT_NORM'])
    print(f"  📊 RUTs únicos activos en ResPets_users: {len(ruts_users)}")
    
    # Procesar duplicados agregando índice de repetición
    print("\n  🔄 Procesando duplicados...")
    df_activos['REPETICION'] = df_activos.groupby('RUT_NORM').cumcount()
    
    # Agregar ceros al RUT según repetición
    def agregar_ceros_por_repeticion(row):
        rut_base = row['RUT_NORM']
        repeticion = row['REPETICION']
        
        if repeticion == 0:
            return rut_base  # Primera aparición, sin cambios
        else:
            # Agregar tantos ceros como repeticiones
            return rut_base + ('0' * repeticion)
    
    df_activos['RUT_CON_CEROS'] = df_activos.apply(agregar_ceros_por_repeticion, axis=1)
    
    # Contar duplicados
    duplicados = df_activos[df_activos['REPETICION'] > 0]
    print(f"  ✓ Registros duplicados transformados: {len(duplicados)}")
    print(f"    - RUTs únicos originales: {df_activos['RUT_NORM'].nunique()}")
    print(f"    - RUTs únicos con ceros: {df_activos['RUT_CON_CEROS'].nunique()}")
    
    # Buscar cuáles NO existen en ResPets_users
    usuarios_a_agregar = []
    encontrados = 0
    
    print("\n  🔍 Verificando existencia en ResPets_users...")
    
    for idx, row in df_activos.iterrows():
        rut_buscar = row['RUT_CON_CEROS']
        
        if rut_buscar not in ruts_users:
            # No existe, hay que agregarlo
            usuarios_a_agregar.append(row)
        else:
            encontrados += 1
    
    print(f"  ✅ Registros encontrados en ResPets_users: {encontrados}")
    print(f"  📝 Registros a agregar (no existen): {len(usuarios_a_agregar)}")
    
    # Generar archivo de ALTAS
    if len(usuarios_a_agregar) > 0:
        print("\n  🔄 Generando archivo de ALTAS con emails únicos...")
        
        # Crear DataFrame de usuarios a agregar
        df_usuarios_agregar = pd.DataFrame(usuarios_a_agregar)
        
        # Obtener emails existentes en ResPets_users
        emails_existentes = set(
            df_users['Email'].dropna().astype(str).str.lower().str.strip()
        )
        print(f"  📧 Emails existentes en ResPets_users: {len(emails_existentes)}")
        
        # Buscar columnas necesarias
        col_nombre = 'nombre_pagador' if 'nombre_pagador' in df_usuarios_agregar.columns else None
        col_apellido_pat = 'apellidopat_pagador' if 'apellidopat_pagador' in df_usuarios_agregar.columns else None
        col_apellido_mat = 'apellidomat_pagador' if 'apellidomat_pagador' in df_usuarios_agregar.columns else None
        col_email = 'titular_email' if 'titular_email' in df_usuarios_agregar.columns else None
        
        print(f"  ✓ Columnas identificadas:")
        print(f"    - Nombre: {col_nombre}")
        print(f"    - Apellido Paterno: {col_apellido_pat}")
        print(f"    - Apellido Materno: {col_apellido_mat}")
        print(f"    - Email: {col_email}")
        
        # Generar emails únicos
        emails_procesados = []
        emails_modificados = 0
        
        for idx, row in df_usuarios_agregar.iterrows():
            email_original = row[col_email] if col_email and pd.notna(row[col_email]) else ''
            email_unico = generar_email_unico(email_original, emails_existentes)
            
            if email_unico != (email_original.lower().strip() if email_original else ''):
                emails_modificados += 1
            
            # Agregar a set para siguientes validaciones
            emails_existentes.add(email_unico)
            emails_procesados.append(email_unico)
        
        print(f"  📧 Emails modificados para evitar duplicados: {emails_modificados}")
        
        # Combinar apellidos
        apellido_completo = ''
        if col_apellido_pat and col_apellido_mat:
            apellido_completo = (df_usuarios_agregar[col_apellido_pat].fillna('').astype(str) + ' ' + 
                               df_usuarios_agregar[col_apellido_mat].fillna('').astype(str)).str.strip()
        elif col_apellido_pat:
            apellido_completo = df_usuarios_agregar[col_apellido_pat].fillna('')
        elif col_apellido_mat:
            apellido_completo = df_usuarios_agregar[col_apellido_mat].fillna('')
        
        # Crear DataFrame de salida
        df_csv_altas = pd.DataFrame({
            'Nombre': df_usuarios_agregar[col_nombre].fillna('') if col_nombre else '',
            'Apellido': apellido_completo,
            'Email': emails_procesados,
            'RUT': df_usuarios_agregar['RUT_CON_CEROS']
        })
        
        archivo_altas = os.path.join(resultado_dir, f'altas_respets_activacion_{timestamp}.csv')
        guardar_csv_formato_especial(df_csv_altas, archivo_altas)
        
        print(f"\n💾 Archivo de ALTAS (activación) generado:")
        print(f"   📄 {os.path.basename(archivo_altas)} ({len(df_csv_altas)} usuarios)")
        
        # Mostrar muestra
        print(f"\n🔍 Muestra de usuarios a agregar (primeros 10):")
        print(df_csv_altas.head(10).to_string(index=False))
        
        # Mostrar ejemplos de RUTs con ceros agregados (duplicados)
        df_con_ceros = df_csv_altas[df_csv_altas['RUT'].str.endswith('0')]
        if len(df_con_ceros) > 0:
            print(f"\n📌 Ejemplos de RUTs con ceros agregados (duplicados): {len(df_con_ceros)} de {len(df_csv_altas)}")
            print(df_con_ceros.head(5)[['Nombre', 'Apellido', 'RUT']].to_string(index=False))
    else:
        print("\n  ✅ No hay usuarios para agregar (todos existen en ResPets_users)")
    
    # ========================================
    # PASO 2: DETECTAR USUARIOS ACTIVOS QUE NO ESTÁN EN BASE ACTIVOS
    # ========================================
    print("\n" + "="*80)
    print("📋 PASO 2: DETECTANDO USUARIOS ACTIVOS QUE NO ESTÁN EN BASE")
    print("="*80)
    
    # Obtener todos los RUTs de la base Activos (con ceros)
    ruts_base_activos_con_ceros = set(df_activos['RUT_CON_CEROS'])
    
    print(f"\n  📊 RUTs en BASE Activos (con ceros): {len(ruts_base_activos_con_ceros)}")
    print(f"  📊 RUTs activos en ResPets_users: {len(ruts_users)}")
    
    # RUTs que están activos en ResPets_users pero NO en BASE Activos
    ruts_activos_no_en_base = ruts_users - ruts_base_activos_con_ceros
    
    print(f"  📝 RUTs activos en ResPets_users que NO están en BASE Activos: {len(ruts_activos_no_en_base)}")
    
    if len(ruts_activos_no_en_base) > 0:
        # Generar archivo de bajas para estos RUTs
        archivo_bajas_no_en_base = os.path.join(resultado_dir, f'bajas_respets_no_en_base_{timestamp}.csv')
        
        df_csv_bajas_no_en_base = pd.DataFrame({
            'RUT': sorted(list(ruts_activos_no_en_base))
        })
        
        guardar_csv_formato_especial(df_csv_bajas_no_en_base, archivo_bajas_no_en_base, solo_rut=True)
        print(f"\n💾 Archivo de BAJAS (usuarios activos no en BASE) generado:")
        print(f"   📄 {os.path.basename(archivo_bajas_no_en_base)} ({len(ruts_activos_no_en_base)} RUTs)")
        
        # Mostrar muestra de estos RUTs
        print(f"\n🔍 Muestra de RUTs a dar de baja (primeros 10):")
        print(df_csv_bajas_no_en_base.head(10).to_string(index=False))
    else:
        print("\n  ✅ Todos los RUTs activos en ResPets_users están en BASE Activos")
    
    # ========================================
    # PASO 3: PROCESAR BAJAS (Inactivos que están activos en ResPets_users)
    # ========================================
    print("\n" + "="*80)
    print("📋 PASO 3: PROCESANDO BAJAS (usuarios en hoja Inactivos)")
    print("="*80)
    
    # Verificar columnas necesarias en Inactivos
    if 'rut_pagador' not in df_inactivos.columns:
        print("  ❌ No se encontró columna 'rut_pagador' en Inactivos")
    else:
        # Normalizar RUTs en Inactivos
        df_inactivos['RUT_NORM'] = df_inactivos['rut_pagador'].apply(normalizar_rut_comparacion)
        df_inactivos = df_inactivos[df_inactivos['RUT_NORM'] != ''].copy()
        print(f"\n  ✓ Registros válidos en Inactivos: {len(df_inactivos)}")
        
        # Obtener RUTs únicos de inactivos
        ruts_inactivos = set(df_inactivos['RUT_NORM'])
        print(f"  📊 RUTs únicos en Inactivos: {len(ruts_inactivos)}")
        
        # IMPORTANTE: Verificar si hay RUTs que están en AMBAS hojas (Activos e Inactivos)
        # Si están en ambas hojas, PREVALECE la hoja Activos (se mantienen activos)
        ruts_en_ambas_hojas = ruts_inactivos & set(df_activos['RUT_NORM'])
        
        if len(ruts_en_ambas_hojas) > 0:
            print(f"\n  ⚠️  RUTs que están en AMBAS hojas (Activos e Inactivos): {len(ruts_en_ambas_hojas)}")
            print(f"      Estos RUTs se MANTIENEN ACTIVOS (prevalece hoja Activos)")
            print(f"      RUTs: {sorted(list(ruts_en_ambas_hojas))}")
            
            # Excluir estos RUTs de la lista de inactivos
            ruts_inactivos = ruts_inactivos - ruts_en_ambas_hojas
            print(f"  📊 RUTs únicamente en Inactivos (excluyendo duplicados): {len(ruts_inactivos)}")
        
        # Buscar cuáles están activos en ResPets_users
        ruts_a_desactivar = []
        
        for rut in ruts_inactivos:
            # Verificar si está en ResPets_users y está activo
            usuario_en_users = df_users[df_users['RUT_NORM'] == rut]
            
            if len(usuario_en_users) > 0:
                # Existe en ResPets_users, verificar si está activo
                if usuario_en_users.iloc[0]['Estado'] == True:
                    ruts_a_desactivar.append(rut)
        
        print(f"  📝 RUTs a desactivar (en Inactivos pero activos en ResPets_users): {len(ruts_a_desactivar)}")
        
        if len(ruts_a_desactivar) > 0:
            # Generar archivo de BAJAS
            archivo_bajas = os.path.join(resultado_dir, f'bajas_respets_desactivacion_{timestamp}.csv')
            
            df_csv_bajas = pd.DataFrame({
                'RUT': sorted(ruts_a_desactivar)
            })
            
            guardar_csv_formato_especial(df_csv_bajas, archivo_bajas, solo_rut=True)
            
            print(f"\n💾 Archivo de BAJAS (desactivación) generado:")
            print(f"   📄 {os.path.basename(archivo_bajas)} ({len(df_csv_bajas)} RUTs)")
            
            # Mostrar muestra
            print(f"\n🔍 Muestra de RUTs a desactivar (primeros 10):")
            print(df_csv_bajas.head(10).to_string(index=False))
        else:
            print("\n  ✅ No hay usuarios para desactivar")
    
    print("\n" + "="*80)
    print("✅ Proceso completado")
    print("="*80)
    
    # Resumen final
    print("\n📊 RESUMEN FINAL:")
    print(f"  • Usuarios que deberían estar activos (Base Activos): {len(ruts_base_activos_con_ceros)}")
    print(f"  • Usuarios actualmente activos (ResPets_users): {len(ruts_users)}")
    print(f"  • Usuarios a AGREGAR: {len(usuarios_a_agregar)}")
    print(f"  • Usuarios a DESACTIVAR (no en Base): {len(ruts_activos_no_en_base) if 'ruts_activos_no_en_base' in locals() else 0}")
    print(f"  • Usuarios a DESACTIVAR (en Inactivos): {len(ruts_a_desactivar) if 'ruts_a_desactivar' in locals() else 0}")
    
    # Calcular total único de bajas
    total_bajas_unico = len(ruts_activos_no_en_base) if 'ruts_activos_no_en_base' in locals() else 0
    if 'ruts_a_desactivar' in locals():
        # Unión para evitar contar duplicados
        todas_bajas = (ruts_activos_no_en_base if 'ruts_activos_no_en_base' in locals() else set()) | set(ruts_a_desactivar)
        total_bajas_unico = len(todas_bajas)
    
    print(f"  • Total ÚNICO de bajas: {total_bajas_unico}")
    
    total_final = len(ruts_users) - total_bajas_unico + len(usuarios_a_agregar)
    print(f"  • Total después de cambios: {total_final} (debería ser {len(ruts_base_activos_con_ceros)})")


if __name__ == "__main__":
    comparar_respets()
