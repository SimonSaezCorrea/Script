"""
Script para comparar datos entre archivo de Base MAPFRE Hogar y archivo BICE MAPFRE.

Proceso especial:
1. BAJAS: Extrae todos los registros con "baja" en columna "Comentarios" para desactivación
2. TRANSFORMACIÓN: Duplicados en BASE se transforman agregando ceros a la derecha
   - Ejemplo: 123456789, 123456789, 123456789 → 123456789, 1234567890, 12345678900
3. ALTAS: Busca RUTs transformados que NO existen en MAPFRE y los agrega
4. BAJAS (no en BASE): Detecta RUTs en MAPFRE que NO están en BASE y los da de baja
5. EMAILS: Maneja duplicados agregando -copy, --copy, ---copy, etc. hasta que no exista

Archivos esperados en carpeta `data/Mapfre`:
- Base de Ene26.xlsx (BASE CLIENTE)
- MAPFRE - Hogar_users_[fecha].xlsx (BASE ACTUAL MAPFRE)
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


def normalizar_cod_docum(cod):
    """
    Normaliza COD_DOCUM eliminando ceros a la izquierda y limpiando.
    """
    if not cod or pd.isna(cod):
        return ''
    
    # Convertir a string y limpiar
    cod_str = str(cod).strip().replace('.', '').replace('-', '').replace(' ', '').upper()
    
    if not cod_str:
        return ''
    
    # Eliminar ceros a la izquierda
    cod_str = cod_str.lstrip('0')
    
    # Si quedó vacío después de eliminar ceros, retornar vacío
    if not cod_str:
        return ''
    
    return cod_str


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


def comparar_mapfre():
    """
    Compara los datos entre Base MAPFRE y archivo BICE MAPFRE.
    """
    # Rutas de archivos
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, 'data', 'Mapfre')
    
    # Buscar archivos dinámicamente
    archivo_base = None
    archivo_mapfre = None
    
    if not os.path.exists(data_dir):
        print(f"❌ Error: no existe la carpeta de datos: {data_dir}")
        return
    
    for filename in os.listdir(data_dir):
        # Ignorar archivos temporales de Excel
        if filename.startswith('~$'):
            continue
            
        if 'Base de Ene26' in filename:
            archivo_base = os.path.join(data_dir, filename)
        elif 'MAPFRE' in filename and '_users_' in filename:
            archivo_mapfre = os.path.join(data_dir, filename)
    
    if not archivo_base or not archivo_mapfre:
        print("❌ Error: No se encontraron todos los archivos necesarios")
        print(f"   Base encontrada: {archivo_base is not None}")
        print(f"   MAPFRE encontrado: {archivo_mapfre is not None}")
        return
    
    print("="*80)
    print("📊 COMPARACIÓN BASE vs MAPFRE - MAPFRE HOGAR")
    print("="*80)
    print(f"\nArchivo Base: {os.path.basename(archivo_base)}")
    print(f"Archivo MAPFRE: {os.path.basename(archivo_mapfre)}")
    
    # Crear carpeta de resultado
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    resultado_dir = os.path.join(script_dir, 'resultado')
    os.makedirs(resultado_dir, exist_ok=True)
    
    # Leer archivos
    print("\n🔄 Leyendo archivos...")
    
    try:
        df_base = pd.read_excel(archivo_base)
        print(f"  ✓ Archivo Base leído correctamente ({len(df_base)} registros)")
    except Exception as e:
        print(f"  ❌ Error al leer archivo Base: {e}")
        return
    
    try:
        df_mapfre = pd.read_excel(archivo_mapfre)
        print(f"  ✓ Archivo MAPFRE leído correctamente ({len(df_mapfre)} registros)")
    except Exception as e:
        print(f"  ❌ Error al leer archivo MAPFRE: {e}")
        return
    
    # ========================================
    # PASO 1: PROCESAR BAJAS (Comentarios = "baja")
    # ========================================
    print("\n" + "="*60)
    print("📋 PASO 1: PROCESANDO BAJAS")
    print("="*60)
    
    if 'COMENTARIOS' in df_base.columns and 'COD_DOCUM' in df_base.columns:
        # Filtrar registros con "baja" en comentarios
        df_bajas = df_base[
            df_base['COMENTARIOS'].astype(str).str.lower().str.contains('baja', na=False)
        ].copy()
        
        print(f"\n  🔍 Registros con 'baja' en Comentarios: {len(df_bajas)}")
        
        if len(df_bajas) > 0:
            # Normalizar COD_DOCUM
            df_bajas['RUT_NORM'] = df_bajas['COD_DOCUM'].apply(normalizar_cod_docum)
            df_bajas = df_bajas[df_bajas['RUT_NORM'] != ''].copy()
            df_bajas_unicos = df_bajas.drop_duplicates(subset=['RUT_NORM']).copy()
            
            # Generar archivo de bajas
            archivo_bajas = os.path.join(resultado_dir, f'bajas_mapfre_desactivacion_{timestamp}.csv')
            
            df_csv_bajas = pd.DataFrame({
                'RUT': df_bajas_unicos['RUT_NORM']
            })
            
            guardar_csv_formato_especial(df_csv_bajas, archivo_bajas, solo_rut=True)
            print(f"\n💾 Archivo de BAJAS (desactivación) generado:")
            print(f"   📄 {os.path.basename(archivo_bajas)} ({len(df_bajas_unicos)} RUTs únicos)")
        else:
            print("\n  ✅ No se encontraron bajas para procesar")
    else:
        print("\n  ⚠️  No se encontró columna 'COMENTARIOS' o 'COD_DOCUM'")
    
    # ========================================
    # PASO 2: TRANSFORMAR DUPLICADOS AGREGANDO CEROS A LA DERECHA
    # ========================================
    print("\n" + "="*60)
    print("📋 PASO 2: PROCESANDO DUPLICADOS CON CEROS A LA DERECHA")
    print("="*60)
    
    # Verificar columnas necesarias
    if 'COD_DOCUM' not in df_base.columns:
        print("  ❌ No se encontró columna 'COD_DOCUM' en Base")
        return
    
    if 'RUT' not in df_mapfre.columns and 'Rut' not in df_mapfre.columns:
        print("  ❌ No se encontró columna 'RUT' o 'Rut' en MAPFRE")
        return
    
    # Determinar nombre de columna RUT en MAPFRE
    col_rut_mapfre = 'RUT' if 'RUT' in df_mapfre.columns else 'Rut'
    
    # Filtrar activos en MAPFRE
    if 'Estado' in df_mapfre.columns:
        total_mapfre = len(df_mapfre)
        df_mapfre = filtrar_activos(df_mapfre, 'Estado')
        print(f"\n  🔍 Registros activos en MAPFRE: {len(df_mapfre)} de {total_mapfre}")
    
    # Normalizar COD_DOCUM en Base (excluir bajas)
    df_base_sin_bajas = df_base[
        ~df_base['COMENTARIOS'].astype(str).str.lower().str.contains('baja', na=False)
    ].copy() if 'COMENTARIOS' in df_base.columns else df_base.copy()
    
    df_base_sin_bajas['RUT_NORM'] = df_base_sin_bajas['COD_DOCUM'].apply(normalizar_cod_docum)
    df_base_sin_bajas = df_base_sin_bajas[df_base_sin_bajas['RUT_NORM'] != ''].copy()
    
    print(f"  ✓ Registros válidos en Base (sin bajas): {len(df_base_sin_bajas)}")
    
    # Normalizar RUT en MAPFRE
    df_mapfre['RUT_NORM'] = df_mapfre[col_rut_mapfre].apply(normalizar_rut_comparacion)
    df_mapfre = df_mapfre[df_mapfre['RUT_NORM'] != ''].copy()
    
    print(f"  ✓ Registros válidos en MAPFRE: {len(df_mapfre)}")
    
    # Obtener set de RUTs que existen en MAPFRE
    ruts_mapfre = set(df_mapfre['RUT_NORM'])
    print(f"  📊 RUTs únicos en MAPFRE: {len(ruts_mapfre)}")
    
    # Procesar duplicados agregando ceros a la derecha
    print("\n  🔄 Transformando duplicados agregando ceros...")
    
    # Agrupar por RUT_NORM y agregar columna con índice de repetición
    df_base_sin_bajas['REPETICION'] = df_base_sin_bajas.groupby('RUT_NORM').cumcount()
    
    # Agregar ceros según repetición: 0 ceros para primera aparición, 1 cero para segunda, etc.
    def agregar_ceros_por_repeticion(row):
        rut_base = row['RUT_NORM']
        repeticion = row['REPETICION']
        
        if repeticion == 0:
            return rut_base  # Primera aparición, sin cambios
        else:
            # Agregar tantos ceros como repeticiones (1ra repetición = 1 cero, 2da = 2 ceros, etc.)
            return rut_base + ('0' * repeticion)
    
    df_base_sin_bajas['RUT_CON_CEROS'] = df_base_sin_bajas.apply(agregar_ceros_por_repeticion, axis=1)
    
    # Contar cuántos duplicados se transformaron
    duplicados = df_base_sin_bajas[df_base_sin_bajas['REPETICION'] > 0]
    print(f"  ✓ Documentos duplicados transformados: {len(duplicados)}")
    print(f"    - Documentos únicos originales: {df_base_sin_bajas['RUT_NORM'].nunique()}")
    print(f"    - Documentos únicos con ceros: {df_base_sin_bajas['RUT_CON_CEROS'].nunique()}")
    
    # Buscar cuáles NO existen en MAPFRE
    usuarios_a_agregar = []
    encontrados = 0
    
    print("\n  🔍 Verificando existencia en MAPFRE...")
    
    for idx, row in df_base_sin_bajas.iterrows():
        rut_buscar = row['RUT_CON_CEROS']
        
        if rut_buscar not in ruts_mapfre:
            # No existe, hay que agregarlo
            usuarios_a_agregar.append(row)
        else:
            encontrados += 1
    
    print(f"  ✅ Documentos encontrados en MAPFRE: {encontrados}")
    print(f"  📝 Documentos a agregar (no existen): {len(usuarios_a_agregar)}")
    
    # ========================================
    # PASO 2.1: DETECTAR USUARIOS EN MAPFRE QUE NO ESTÁN EN BASE
    # ========================================
    print("\n" + "="*60)
    print("📋 PASO 2.1: DETECTANDO USUARIOS EN MAPFRE NO EN BASE")
    print("="*60)
    
    # Obtener todos los RUTs de la base (con ceros)
    ruts_base_con_ceros = set(df_base_sin_bajas['RUT_CON_CEROS'])
    
    print(f"\n  📊 RUTs en BASE (con ceros): {len(ruts_base_con_ceros)}")
    print(f"  📊 RUTs en MAPFRE: {len(ruts_mapfre)}")
    
    # RUTs que están en MAPFRE pero NO en BASE
    ruts_mapfre_no_en_base = ruts_mapfre - ruts_base_con_ceros
    
    print(f"  📝 RUTs en MAPFRE que NO están en BASE: {len(ruts_mapfre_no_en_base)}")
    
    if len(ruts_mapfre_no_en_base) > 0:
        # Generar archivo de bajas para estos RUTs
        archivo_bajas_no_en_base = os.path.join(resultado_dir, f'bajas_mapfre_no_en_base_{timestamp}.csv')
        
        df_csv_bajas_no_en_base = pd.DataFrame({
            'RUT': sorted(list(ruts_mapfre_no_en_base))
        })
        
        guardar_csv_formato_especial(df_csv_bajas_no_en_base, archivo_bajas_no_en_base, solo_rut=True)
        print(f"\n💾 Archivo de BAJAS (usuarios en MAPFRE no en BASE) generado:")
        print(f"   📄 {os.path.basename(archivo_bajas_no_en_base)} ({len(ruts_mapfre_no_en_base)} RUTs)")
        
        # Mostrar muestra de estos RUTs
        print(f"\n🔍 Muestra de RUTs a dar de baja (primeros 10):")
        print(df_csv_bajas_no_en_base.head(10).to_string(index=False))
    else:
        print("\n  ✅ Todos los RUTs en MAPFRE existen en BASE")
    
    # ========================================
    # PASO 3: GENERAR ARCHIVO DE ALTAS CON EMAILS ÚNICOS
    # ========================================
    print("\n" + "="*60)
    print("📋 PASO 3: GENERANDO ARCHIVO DE ALTAS (con emails únicos)")
    print("="*60)
    
    if len(usuarios_a_agregar) > 0:
        # Crear DataFrame de usuarios a agregar
        df_usuarios_agregar = pd.DataFrame(usuarios_a_agregar)
        
        # Obtener emails existentes en MAPFRE
        col_email_mapfre = None
        for col in ['Email', 'EMAIL', 'email', 'Correo', 'CORREO', 'Mail', 'MAIL']:
            if col in df_mapfre.columns:
                col_email_mapfre = col
                break
        
        emails_existentes = set()
        if col_email_mapfre:
            emails_existentes = set(
                df_mapfre[col_email_mapfre].dropna().astype(str).str.lower().str.strip()
            )
        
        print(f"\n  📧 Emails existentes en MAPFRE: {len(emails_existentes)}")
        
        # Buscar columnas necesarias en Base
        columnas_posibles = {
            'nombre': ['NOMBRE', 'Nombre', 'nombre', 'NOMBRES', 'Nombres'],
            'apellido_pat': ['APATERNO', 'Apellido Pat.', 'Apellido Paterno', 'ApellidoPaterno'],
            'apellido_mat': ['AMATERNO', 'Apellido Mat.', 'Apellido Materno', 'ApellidoMaterno'],
            'email': ['CORREO 1', 'CORREO1', 'EMAIL', 'Email', 'email', 'CORREO', 'Correo', 'MAIL', 'Mail']
        }
        
        def encontrar_columna(df, opciones):
            for col in opciones:
                if col in df.columns:
                    return col
            return None
        
        col_nombre = encontrar_columna(df_usuarios_agregar, columnas_posibles['nombre'])
        col_apellido_pat = encontrar_columna(df_usuarios_agregar, columnas_posibles['apellido_pat'])
        col_apellido_mat = encontrar_columna(df_usuarios_agregar, columnas_posibles['apellido_mat'])
        col_email = encontrar_columna(df_usuarios_agregar, columnas_posibles['email'])
        
        print(f"  ✓ Columnas identificadas:")
        print(f"    - Nombre: {col_nombre}")
        print(f"    - Apellido Paterno: {col_apellido_pat}")
        print(f"    - Apellido Materno: {col_apellido_mat}")
        print(f"    - Email: {col_email}")
        
        # Generar emails únicos
        emails_procesados = []
        emails_modificados = 0
        
        for idx, row in df_usuarios_agregar.iterrows():
            email_original = row[col_email] if col_email else ''
            email_unico = generar_email_unico(email_original, emails_existentes)
            
            if email_unico != email_original.lower().strip() if email_original else False:
                emails_modificados += 1
            
            # Agregar a set para siguientes validaciones
            emails_existentes.add(email_unico)
            emails_procesados.append(email_unico)
        
        print(f"\n  📧 Emails modificados para evitar duplicados: {emails_modificados}")
        
        # Combinar apellidos paterno y materno
        apellido_completo = ''
        if col_apellido_pat and col_apellido_mat:
            apellido_completo = (df_usuarios_agregar[col_apellido_pat].fillna('').astype(str) + ' ' + 
                               df_usuarios_agregar[col_apellido_mat].fillna('').astype(str)).str.strip()
        elif col_apellido_pat:
            apellido_completo = df_usuarios_agregar[col_apellido_pat].fillna('')
        elif col_apellido_mat:
            apellido_completo = df_usuarios_agregar[col_apellido_mat].fillna('')
        
        # Crear DataFrame de salida usando RUT_CON_CEROS
        df_csv_altas = pd.DataFrame({
            'Nombre': df_usuarios_agregar[col_nombre].fillna('') if col_nombre else '',
            'Apellido': apellido_completo,
            'Email': emails_procesados,
            'RUT': df_usuarios_agregar['RUT_CON_CEROS']  # Usar el RUT con ceros agregados
        })
        
        archivo_altas = os.path.join(resultado_dir, f'altas_mapfre_activacion_{timestamp}.csv')
        guardar_csv_formato_especial(df_csv_altas, archivo_altas)
        
        print(f"\n💾 Archivo de ALTAS (activación) generado:")
        print(f"   📄 {os.path.basename(archivo_altas)} ({len(df_csv_altas)} usuarios)")
        
        # Mostrar muestra
        print(f"\n🔍 Muestra de usuarios a agregar (primeros 10):")
        print(df_csv_altas.head(10).to_string(index=False))
        
        # Mostrar ejemplos de RUTs con ceros agregados
        df_con_ceros = df_csv_altas[df_csv_altas['RUT'].str.endswith('0')]
        if len(df_con_ceros) > 0:
            print(f"\n📌 Ejemplos de RUTs con ceros agregados (duplicados): {len(df_con_ceros)} de {len(df_csv_altas)}")
            print(df_con_ceros.head(5)[['Nombre', 'Apellido', 'RUT']].to_string(index=False))
    else:
        print("\n  ✅ No hay usuarios para agregar (todos existen en MAPFRE)")
    
    print("\n" + "="*80)
    print("✅ Proceso completado")
    print("="*80)


if __name__ == "__main__":
    comparar_mapfre()
