"""
Script para comparar datos entre Base Pawer - Hogar 2026 y Pacifico Hogar usuarios.

Estructura archivo "Base Pawer - Hogar 2026":
- Columna A: N° Documento (RUT)
- Columna B: Nombres y Apellidos (separar según regla)
- Columna D: Mail (email)

Reglas para separar nombres y apellidos (Columna B):
- 4 palabras: 2 primeras = nombres, 2 últimas = apellidos
- 3 palabras: 1ra = nombre, 2da y 3ra = apellidos
- 2 palabras: 1ra = nombre, 2da = apellido
- 5 o más palabras: generar archivo extra de supervisión manual

Archivos esperados en carpeta `data/Pacifico Hogar`:
- Base Pawer - Hogar 2026.xlsx (PAWER - Base a comparar)
- Pacifico Hogar_users_*.xlsx (Usuarios existentes a completar)
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
    imprimir_resumen
)
from utils.normalizers import combinar_rut_dv


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


def separar_nombres_apellidos(nombre_completo):
    """
    Separa nombres y apellidos según las reglas especificadas.
    
    Args:
        nombre_completo: string con el nombre completo
    
    Returns:
        tuple (nombre, apellido, requiere_revision)
        - requiere_revision=True si tiene 5 o más palabras
    """
    if not nombre_completo or pd.isna(nombre_completo):
        return '', '', False
    
    # Limpiar y dividir
    nombre_completo = str(nombre_completo).strip()
    palabras = nombre_completo.split()
    
    num_palabras = len(palabras)
    
    if num_palabras == 0:
        return '', '', False
    elif num_palabras == 1:
        return palabras[0], '', False
    elif num_palabras == 2:
        # 1ra = nombre, 2da = apellido
        return palabras[0], palabras[1], False
    elif num_palabras == 3:
        # 1ra = nombre, 2da y 3ra = apellidos
        return palabras[0], ' '.join(palabras[1:3]), False
    elif num_palabras == 4:
        # 2 primeras = nombres, 2 últimas = apellidos
        return ' '.join(palabras[0:2]), ' '.join(palabras[2:4]), False
    else:
        # 5 o más palabras: requiere revisión manual
        return nombre_completo, '', True


def normalizar_ruts_dataframe_pacifico(df, col_rut):
    """
    Normaliza RUTs en un DataFrame para comparación.
    """
    # Normalizar RUTs
    df['RUT_NORM'] = df[col_rut].apply(normalizar_rut_comparacion)
    
    # Filtrar solo RUTs válidos
    df = df[df['RUT_NORM'].notna() & (df['RUT_NORM'] != '')].copy()
    
    # Crear columna RUT limpia para mostrar
    df['RUT'] = df['RUT_NORM']
    
    return df


def procesar_base_pawer(archivo_base):
    """
    Procesa el archivo Base Pawer separando nombres y apellidos.
    
    Returns:
        tuple (df_procesado, df_requiere_revision)
    """
    # Leer archivo (sin encabezado ya que usa columnas A, B, D)
    df = pd.read_excel(archivo_base, header=None)
    
    # Renombrar columnas según la estructura
    # Columna A (índice 0): RUT
    # Columna B (índice 1): Nombres y Apellidos
    # Columna C (índice 2): no se usa
    # Columna D (índice 3): Email
    
    # Verificar si tiene encabezado
    if isinstance(df.iloc[0, 0], str) and not str(df.iloc[0, 0]).replace('.', '').replace('-', '').isdigit():
        # Tiene encabezado, omitir primera fila
        df = df.iloc[1:].reset_index(drop=True)
    
    # Asignar nombres a columnas relevantes
    df_procesado = pd.DataFrame({
        'RUT_ORIGINAL': df.iloc[:, 0],  # Columna A
        'NOMBRE_COMPLETO': df.iloc[:, 1],  # Columna B
        'EMAIL': df.iloc[:, 3] if len(df.columns) > 3 else ''  # Columna D
    })
    
    # Separar nombres y apellidos
    df_procesado[['NOMBRE', 'APELLIDO', 'REQUIERE_REVISION']] = df_procesado['NOMBRE_COMPLETO'].apply(
        lambda x: pd.Series(separar_nombres_apellidos(x))
    )
    
    # Separar registros que requieren revisión
    df_requiere_revision = df_procesado[df_procesado['REQUIERE_REVISION'] == True].copy()
    df_procesado = df_procesado[df_procesado['REQUIERE_REVISION'] == False].copy()
    
    # Normalizar RUTs
    df_procesado = normalizar_ruts_dataframe_pacifico(df_procesado, 'RUT_ORIGINAL')
    
    if len(df_requiere_revision) > 0:
        df_requiere_revision = normalizar_ruts_dataframe_pacifico(df_requiere_revision, 'RUT_ORIGINAL')
    else:
        # Crear DataFrame vacío con las mismas columnas si no hay registros
        df_requiere_revision = pd.DataFrame(columns=df_procesado.columns)
    
    return df_procesado, df_requiere_revision


def comparar_pacifico_hogar():
    """
    Compara los RUTs entre Base Pawer y Pacifico Hogar usuarios.
    Maneja duplicados agregando ceros a los RUTs y -copy a los emails.
    """
    # Rutas de archivos
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, 'data', 'Pacifico Hogar')
    resultado_dir = os.path.join(script_dir, 'resultado')
    
    # Crear carpeta de resultados si no existe
    os.makedirs(resultado_dir, exist_ok=True)
    
    # Buscar archivos dinámicamente
    archivo_base = None
    archivo_usuarios = None
    
    if not os.path.exists(data_dir):
        print(f"❌ Error: no existe la carpeta de datos: {data_dir}")
        return
    
    for filename in os.listdir(data_dir):
        # Ignorar archivos temporales de Excel
        if filename.startswith('~$'):
            continue
        
        if 'Base Pawer' in filename or 'Base pawer' in filename:
            archivo_base = os.path.join(data_dir, filename)
        elif 'Pacifico Hogar_users' in filename or 'Pacifico_Hogar_users' in filename:
            archivo_usuarios = os.path.join(data_dir, filename)
    
    if not archivo_base or not archivo_usuarios:
        print("❌ Error: No se encontraron todos los archivos necesarios")
        print(f"   Base Pawer encontrado: {archivo_base is not None}")
        print(f"   Pacifico Hogar usuarios encontrado: {archivo_usuarios is not None}")
        return
    
    print("="*80)
    print("📊 COMPARACIÓN BASE PAWER vs PACIFICO HOGAR USUARIOS")
    print("="*80)
    print(f"\nArchivo Base Pawer: {os.path.basename(archivo_base)}")
    print(f"Archivo Usuarios: {os.path.basename(archivo_usuarios)}")
    
    # Leer y procesar Base Pawer
    print("\n🔄 Procesando Base Pawer...")
    try:
        df_base, df_revision = procesar_base_pawer(archivo_base)
        print(f"  ✓ Base Pawer procesada correctamente")
        print(f"  - Registros procesados: {len(df_base)}")
        if len(df_revision) > 0:
            print(f"  ⚠️  Registros que requieren revisión manual: {len(df_revision)}")
    except Exception as e:
        print(f"  ❌ Error al procesar Base Pawer: {e}")
        return
    
    # Leer archivo de usuarios
    print("\n🔄 Leyendo archivo de usuarios...")
    try:
        df_usuarios = pd.read_excel(archivo_usuarios)
        print(f"  ✓ Archivo de usuarios leído correctamente")
        print(f"  - Registros totales: {len(df_usuarios)}")
    except Exception as e:
        print(f"  ❌ Error al leer archivo de usuarios: {e}")
        return
    
    # Filtrar solo registros activos en usuarios si existe columna 'Estado'
    total_usuarios = len(df_usuarios)
    if 'Estado' in df_usuarios.columns:
        # Mostrar distribución de estados antes de filtrar
        print(f"  - Distribución de estados:")
        estados_count = df_usuarios['Estado'].value_counts()
        for estado, count in estados_count.items():
            print(f"      {estado}: {count}")
        
        df_usuarios = filtrar_activos(df_usuarios, 'Estado')
        print(f"  - Usuarios activos: {len(df_usuarios)} ({total_usuarios - len(df_usuarios)} inactivos filtrados)")
    
    # Normalizar RUTs en archivo de usuarios
    if 'RUT' in df_usuarios.columns:
        df_usuarios = normalizar_ruts_dataframe_pacifico(df_usuarios, 'RUT')
        print(f"  ✓ RUTs normalizados en usuarios: {len(df_usuarios)}")
    else:
        print("  ⚠️  No se encontró columna 'RUT' en archivo de usuarios")
    
    # Obtener sets de RUTs únicos
    ruts_base = set(df_base['RUT_NORM'].unique())  # RUTs originales sin transformar
    
    # IMPORTANTE: Incluir también los RUTs que requieren revisión manual
    # ya que SON parte de la Base Pawer
    if len(df_revision) > 0:
        ruts_revision = set(df_revision['RUT_NORM'].unique())
        ruts_base = ruts_base | ruts_revision  # Unión de ambos conjuntos
        print(f"\n  ℹ️  Se incluyeron {len(ruts_revision)} RUTs de revisión manual en la comparación")
    
    ruts_usuarios = set(df_usuarios['RUT_NORM'].unique()) if 'RUT_NORM' in df_usuarios.columns else set()
    
    print(f"\n🔢 RUTs únicos:")
    print(f"  - Base Pawer (originales + revisión): {len(ruts_base)}")
    print(f"  - Usuarios: {len(ruts_usuarios)}")
    
    # ========================================
    # TRANSFORMAR DUPLICADOS AGREGANDO CEROS A LA DERECHA
    # ========================================
    print("\n" + "="*60)
    print("📋 PROCESANDO DUPLICADOS CON CEROS A LA DERECHA")
    print("="*60)
    
    # Combinar df_base y df_revision para la transformación de duplicados
    df_base_completa = pd.concat([df_base, df_revision], ignore_index=True) if len(df_revision) > 0 else df_base
    
    # Agrupar por RUT_NORM y agregar columna con índice de repetición
    df_base_completa['REPETICION'] = df_base_completa.groupby('RUT_NORM').cumcount()
    
    # Agregar ceros según repetición: 0 ceros para primera aparición, 1 cero para segunda, etc.
    def agregar_ceros_por_repeticion(row):
        rut_base = row['RUT_NORM']
        repeticion = row['REPETICION']
        
        if repeticion == 0:
            return rut_base  # Primera aparición, sin cambios
        else:
            # Agregar tantos ceros como repeticiones (1ra repetición = 1 cero, 2da = 2 ceros, etc.)
            return rut_base + ('0' * repeticion)
    
    df_base_completa['RUT_CON_CEROS'] = df_base_completa.apply(agregar_ceros_por_repeticion, axis=1)
    
    # Actualizar df_base y df_revision con RUT_CON_CEROS
    # Separar nuevamente usando la columna REQUIERE_REVISION si existe
    if 'REQUIERE_REVISION' in df_base_completa.columns:
        df_base = df_base_completa[df_base_completa['REQUIERE_REVISION'] == False].copy()
        df_revision = df_base_completa[df_base_completa['REQUIERE_REVISION'] == True].copy()
    else:
        df_base = df_base_completa.copy()
    
    # Contar cuántos duplicados se transformaron
    duplicados = df_base_completa[df_base_completa['REPETICION'] > 0]
    total_duplicados = len(duplicados)
    print(f"\n  ✓ Documentos duplicados transformados: {total_duplicados}")
    if total_duplicados > 0:
        print(f"    - Documentos únicos originales: {df_base_completa['RUT_NORM'].nunique()}")
        print(f"    - Documentos únicos con ceros: {df_base_completa['RUT_CON_CEROS'].nunique()}")
        print(f"\n  📌 Ejemplos de RUTs transformados (primeros 5):")
        for idx, row in duplicados.head(5).iterrows():
            print(f"      {row['RUT_NORM']} → {row['RUT_CON_CEROS']} (repetición {int(row['REPETICION'])})")
    
    # Realizar comparaciones usando RUT_CON_CEROS
    print("\n🔍 Realizando comparaciones...")
    
    ruts_base_con_ceros = set(df_base_completa['RUT_CON_CEROS'].unique())
    coincidencias = ruts_base_con_ceros & ruts_usuarios
    base_no_en_usuarios = ruts_base_con_ceros - ruts_usuarios
    usuarios_no_en_base = ruts_usuarios - ruts_base_con_ceros
    
    print(f"\n📊 Resultados de la comparación:")
    print(f"  ✓ Coincidencias: {len(coincidencias)}")
    print(f"  ➕ En Base Pawer pero NO en Usuarios: {len(base_no_en_usuarios)}")
    print(f"  ➖ En Usuarios pero NO en Base Pawer: {len(usuarios_no_en_base)}")
    print(f"\n  📝 Nota: Los RUTs duplicados en Base Pawer fueron transformados agregando '0', '00', etc.")
    
    # Guardar resultados
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Guardar archivo de revisión manual (5+ palabras)
    # Solo si NO están ya en el sistema de usuarios
    df_revision_filtrado = df_revision[~df_revision['RUT_CON_CEROS'].isin(ruts_usuarios)].copy() if len(df_revision) > 0 else df_revision
    
    if len(df_revision_filtrado) > 0:
        archivo_revision = os.path.join(resultado_dir, f'pacifico_hogar_revision_manual_{timestamp}.csv')
        df_revision_export = df_revision_filtrado[['RUT_CON_CEROS', 'NOMBRE_COMPLETO', 'EMAIL']].copy()
        df_revision_export.columns = ['RUT', 'NOMBRE_COMPLETO', 'EMAIL']  # Renombrar para claridad
        df_revision_export.to_csv(archivo_revision, index=False, encoding='utf-8-sig')
        print(f"\n⚠️  Archivo de revisión manual guardado: {os.path.basename(archivo_revision)}")
        print(f"   Total de registros que requieren revisión: {len(df_revision_filtrado)}")
        if len(df_revision) > len(df_revision_filtrado):
            print(f"   ({len(df_revision) - len(df_revision_filtrado)} ya estaban en el sistema y fueron omitidos)")
    
    # 2. Guardar registros en Base Pawer pero no en Usuarios (los que hay que agregar)
    if len(base_no_en_usuarios) > 0:
        # Usar RUT_CON_CEROS para filtrar de df_base_completa
        df_agregar = df_base_completa[df_base_completa['RUT_CON_CEROS'].isin(base_no_en_usuarios)].copy()
        archivo_agregar = os.path.join(resultado_dir, f'pacifico_hogar_para_agregar_{timestamp}.csv')
        
        # Obtener emails existentes en el sistema
        print("\n  📧 Procesando emails únicos...")
        emails_existentes = set()
        if 'Email' in df_usuarios.columns:
            emails_existentes = set(
                df_usuarios['Email'].dropna().astype(str).str.lower().str.strip()
            )
        print(f"     Emails existentes en sistema: {len(emails_existentes)}")
        
        # Generar emails únicos
        emails_procesados = []
        emails_modificados = 0
        
        for idx, row in df_agregar.iterrows():
            email_original = row['EMAIL'] if pd.notna(row['EMAIL']) else ''
            email_unico = generar_email_unico(email_original, emails_existentes)
            
            if email_unico != (email_original.lower().strip() if email_original else ''):
                emails_modificados += 1
            
            # Agregar a set para siguientes validaciones
            if email_unico:
                emails_existentes.add(email_unico)
            emails_procesados.append(email_unico)
        
        print(f"     Emails modificados para evitar duplicados: {emails_modificados}")
        
        # Guardar en formato especial: "nombre, apellido, email, rut",
        with open(archivo_agregar, 'w', encoding='utf-8') as f:
            for i, (idx, row) in enumerate(df_agregar.iterrows()):
                # Reemplazar valores NaN con cadena vacía
                nombre = str(row['NOMBRE']) if pd.notna(row['NOMBRE']) else ''
                apellido = str(row['APELLIDO']) if pd.notna(row['APELLIDO']) else ''
                email = emails_procesados[i]  # Usar email procesado
                rut = str(row['RUT_CON_CEROS'])  # Usar RUT con ceros
                
                # Escribir línea en formato: "nombre, apellido, email, rut",
                f.write(f'"{nombre}, {apellido}, {email}, {rut}",\n')
        
        print(f"\n➕ Archivo con registros para agregar guardado: {os.path.basename(archivo_agregar)}")
        print(f"   Total de registros a agregar: {len(df_agregar)}")
        
        # Mostrar ejemplos de RUTs con ceros agregados
        df_con_ceros = df_agregar[df_agregar['RUT_CON_CEROS'].str.endswith('0')]
        if len(df_con_ceros) > 0:
            print(f"\n  📌 Registros con RUTs modificados (duplicados): {len(df_con_ceros)} de {len(df_agregar)}")
            print(f"     Ejemplos (primeros 3):")
            for idx, row in df_con_ceros.head(3).iterrows():
                print(f"       {row['NOMBRE']} {row['APELLIDO']} - RUT: {row['RUT_CON_CEROS']} (original: {row['RUT_NORM']})")
    
    # 3. Guardar coincidencias (para verificación)
    if len(coincidencias) > 0:
        df_coincidencias_base = df_base_completa[df_base_completa['RUT_CON_CEROS'].isin(coincidencias)].copy()
        df_coincidencias_usuarios = df_usuarios[df_usuarios['RUT_NORM'].isin(coincidencias)].copy()
        
        # Merge para ver datos de ambos lados
        df_coincidencias = pd.merge(
            df_coincidencias_base[['RUT_CON_CEROS', 'NOMBRE', 'APELLIDO', 'EMAIL']],
            df_coincidencias_usuarios[['RUT_NORM', 'Nombre', 'Apellido', 'Email']] if all(col in df_coincidencias_usuarios.columns for col in ['Nombre', 'Apellido', 'Email']) else df_coincidencias_usuarios[['RUT_NORM']],
            left_on='RUT_CON_CEROS',
            right_on='RUT_NORM',
            how='left',
            suffixes=('_Base', '_Sistema')
        )
        
        archivo_coincidencias = os.path.join(resultado_dir, f'pacifico_hogar_coincidencias_{timestamp}.csv')
        df_coincidencias.to_csv(archivo_coincidencias, index=False, encoding='utf-8-sig')
        print(f"\n✓ Archivo de coincidencias guardado: {os.path.basename(archivo_coincidencias)}")
    
    # 4. Guardar registros en Usuarios pero no en Base Pawer (posibles bajas/eliminar)
    if len(usuarios_no_en_base) > 0:
        df_solo_usuarios = df_usuarios[df_usuarios['RUT_NORM'].isin(usuarios_no_en_base)].copy()
        archivo_solo_usuarios = os.path.join(resultado_dir, f'pacifico_hogar_para_eliminar_{timestamp}.csv')
        df_solo_usuarios.to_csv(archivo_solo_usuarios, index=False, encoding='utf-8-sig')
        print(f"\n➖ Archivo con registros para eliminar guardado: {os.path.basename(archivo_solo_usuarios)}")
        print(f"   Total de registros a eliminar: {len(df_solo_usuarios)}")
    
    print("\n" + "="*80)
    print("✅ COMPARACIÓN COMPLETADA")
    print("="*80)


if __name__ == '__main__':
    comparar_pacifico_hogar()
