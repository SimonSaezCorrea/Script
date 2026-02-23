"""
Script para generar archivos de carga desde el Excel de Southbridge.

Lee el archivo Excel de Southbridge y genera archivos CSV separados por Canal
en el formato requerido:
    "Nombre,Apellido,Email,Rut",
    "Nombre2,Apellido2,Email2,Rut2",
    ...

Columnas del Excel de entrada:
    N° Póliza | Nombre propietario | Apellido paterno propietario |
    Apellido materno propietario | Rut propietario | Propietario DV |
    Email propietario | Teléfono propietario | Canal

Archivos generados (uno por Canal):
    altas_<canal>.csv  →  e.g. altas_march.csv, altas_sura.csv, etc.

Archivo esperado en carpeta `data/Southbridge`:
    Un único archivo .xlsx con los datos de Southbridge
"""
import pandas as pd
import os
import sys
import re
from datetime import datetime

# Agregar la carpeta padre al path para poder importar utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.normalizers import combinar_rut_dv
from utils.file_handlers import guardar_csv_formato_especial


# ========================
# COLUMNAS DEL EXCEL
# ========================
COL_POLIZA = 'N° Póliza'
COL_NOMBRE = 'Nombre propietario'
COL_APELLIDO_PAT = 'Apellido paterno propietario'
COL_APELLIDO_MAT = 'Apellido materno propietario'
COL_RUT = 'Rut propietario'
COL_DV = 'Propietario DV'
COL_EMAIL = 'Email propietario'
COL_TELEFONO = 'Teléfono propietario'
COL_CANAL = 'Canal'


def normalizar_nombre_campo(texto):
    """
    Normaliza un campo de texto (nombre/apellido): capitaliza y limpia espacios.
    """
    if not texto or pd.isna(texto):
        return ''
    return str(texto).strip().title().replace(r'\s+', ' ')


def normalizar_canal_filename(canal):
    """
    Convierte el nombre del canal en un nombre de archivo válido:
    - Minúsculas
    - Reemplaza espacios con guiones bajos
    - Elimina caracteres especiales
    """
    if not canal or pd.isna(canal):
        return 'sin_canal'
    canal_str = str(canal).strip().lower()
    # Reemplazar caracteres especiales y espacios
    canal_str = re.sub(r'[^a-z0-9áéíóúüñ\s]', '', canal_str)
    canal_str = canal_str.strip().replace(' ', '_')
    # Reemplazar caracteres con tilde para compatibilidad de nombres de archivo
    canal_str = canal_str.replace('á', 'a').replace('é', 'e').replace('í', 'i') \
                         .replace('ó', 'o').replace('ú', 'u').replace('ü', 'u') \
                         .replace('ñ', 'n')
    return canal_str or 'sin_canal'


def normalizar_rut_southbridge(rut, dv):
    """
    Combina y normaliza RUT + DV.
    """
    rut_completo = combinar_rut_dv(rut, dv)
    if not rut_completo or pd.isna(rut_completo):
        return ''
    # Limpiar puntos, guiones y espacios
    rut_str = str(rut_completo).strip().replace('.', '').replace('-', '').replace(' ', '').upper()
    # Eliminar ceros a la izquierda
    rut_str = rut_str.lstrip('0')
    return rut_str


def generar_email_unico(email_base, emails_existentes):
    """
    Genera un email único agregando -copy, --copy, ---copy, etc.
    hasta que no exista en el conjunto de emails existentes.
    """
    if not email_base or pd.isna(email_base) or str(email_base).strip() == '':
        return email_base

    email_base = str(email_base).strip().lower()

    if email_base not in emails_existentes:
        return email_base

    contador = 1
    while True:
        prefijo = '-' * contador + 'copy'
        if '@' in email_base:
            nombre, dominio = email_base.rsplit('@', 1)
            email_nuevo = f"{nombre}{prefijo}@{dominio}"
        else:
            email_nuevo = f"{email_base}{prefijo}"

        if email_nuevo not in emails_existentes:
            return email_nuevo

        contador += 1
        if contador > 10000:
            print(f"  ⚠️  Warning: Email {email_base} generó más de 10000 copias")
            return email_nuevo


def resolver_duplicados(df_canal):
    """
    Resuelve duplicados de RUT y email dentro de un canal:
    - RUTs duplicados: 2ª aparición recibe un cero extra, 3ª dos ceros, etc.
    - Emails duplicados: 2ª aparición recibe -copy, 3ª --copy, etc.

    Returns:
        DataFrame con columnas RUT_FINAL y EMAIL_FINAL ya deduperadas.
    """
    df = df_canal.copy().reset_index(drop=True)

    # ---- RUTs con ceros ----
    df['REPETICION_RUT'] = df.groupby('RUT_NORM').cumcount()
    df['RUT_FINAL'] = df.apply(
        lambda row: row['RUT_NORM'] + ('0' * row['REPETICION_RUT']),
        axis=1
    )

    # ---- Emails con -copy ----
    emails_vistos = set()
    emails_resueltos = []
    for _, row in df.iterrows():
        email_unico = generar_email_unico(row['EMAIL_NORM'], emails_vistos)
        emails_vistos.add(email_unico)
        emails_resueltos.append(email_unico)
    df['EMAIL_FINAL'] = emails_resueltos

    return df


def generar_carga_southbridge():
    """
    Lee el Excel de Southbridge y genera un CSV por cada Canal encontrado.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, 'data', 'Southbridge')
    resultado_dir = os.path.join(script_dir, 'resultado')
    os.makedirs(resultado_dir, exist_ok=True)

    # Buscar archivo Excel en la carpeta de datos
    archivo_excel = None
    for filename in os.listdir(data_dir):
        if filename.startswith('~$'):
            continue
        if filename.endswith(('.xlsx', '.xls')):
            archivo_excel = os.path.join(data_dir, filename)
            break

    if not archivo_excel:
        print("❌ Error: No se encontró ningún archivo .xlsx en la carpeta data/Southbridge")
        return

    print("=" * 80)
    print("📊 GENERADOR DE CARGA - SOUTHBRIDGE")
    print("=" * 80)
    print(f"\nArchivo: {os.path.basename(archivo_excel)}")

    # Leer Excel
    print("\n🔄 Leyendo archivo...")
    try:
        df = pd.read_excel(archivo_excel)
        print(f"  ✓ {len(df)} registros leídos")
    except Exception as e:
        print(f"  ❌ Error al leer el archivo: {e}")
        return

    # Validar columnas requeridas
    columnas_requeridas = [COL_NOMBRE, COL_APELLIDO_PAT, COL_RUT, COL_DV, COL_EMAIL, COL_CANAL]
    columnas_faltantes = [c for c in columnas_requeridas if c not in df.columns]
    if columnas_faltantes:
        print(f"\n❌ Error: Faltan columnas en el archivo:")
        for col in columnas_faltantes:
            print(f"   - {col}")
        print(f"\nColumnas disponibles: {list(df.columns)}")
        return

    # Procesar datos
    print("\n🔧 Procesando datos...")

    # Combinar apellidos
    df['APELLIDO_COMPLETO'] = (
        df[COL_APELLIDO_PAT].fillna('').astype(str).str.strip().str.title() + ' ' +
        df[COL_APELLIDO_MAT].fillna('').astype(str).str.strip().str.title()
    ).str.strip().str.replace(r'\s+', ' ', regex=True)

    # Normalizar nombre
    df['NOMBRE_NORM'] = df[COL_NOMBRE].fillna('').astype(str).str.strip().str.title() \
                                      .str.replace(r'\s+', ' ', regex=True)

    # Combinar RUT + DV
    df['RUT_NORM'] = df.apply(
        lambda row: normalizar_rut_southbridge(row[COL_RUT], row[COL_DV]), axis=1
    )

    # Normalizar email
    df['EMAIL_NORM'] = df[COL_EMAIL].fillna('').astype(str).str.strip().str.lower()

    # Eliminar registros sin RUT válido
    df_validos = df[df['RUT_NORM'] != ''].copy()
    df_sin_rut = df[df['RUT_NORM'] == ''].copy()

    print(f"  ✓ Registros con RUT válido: {len(df_validos)}")
    if len(df_sin_rut) > 0:
        print(f"  ⚠️  Registros sin RUT (serán omitidos): {len(df_sin_rut)}")

    # Eliminar registros sin email
    df_sin_email = df_validos[df_validos['EMAIL_NORM'] == ''].copy()
    df_con_email = df_validos[df_validos['EMAIL_NORM'] != ''].copy()

    if len(df_sin_email) > 0:
        print(f"  ⚠️  Registros sin email (serán omitidos): {len(df_sin_email)}")

    print(f"  ✓ Registros listos para exportar: {len(df_con_email)}")

    # ========================
    # SEPARAR POR CANAL
    # ========================
    canales = df_con_email[COL_CANAL].fillna('Sin canal').unique()
    print(f"\n📂 Canales encontrados: {len(canales)}")
    for canal in sorted(canales):
        print(f"   - {canal}")

    print("\n💾 Generando archivos por canal...")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    archivos_generados = []

    for canal in sorted(canales):
        df_canal = df_con_email[df_con_email[COL_CANAL].fillna('Sin canal') == canal].copy()

        canal_filename = normalizar_canal_filename(canal)
        nombre_archivo = f'altas_{canal_filename}.csv'
        ruta_archivo = os.path.join(resultado_dir, nombre_archivo)

        # Resolver duplicados de RUT y email
        df_canal = resolver_duplicados(df_canal)

        ruts_con_ceros = (df_canal['REPETICION_RUT'] > 0).sum()
        emails_con_copy = (df_canal['EMAIL_FINAL'] != df_canal['EMAIL_NORM']).sum()

        # Preparar DataFrame en el formato requerido
        df_export = pd.DataFrame({
            'Nombre': df_canal['NOMBRE_NORM'].values,
            'Apellido': df_canal['APELLIDO_COMPLETO'].values,
            'Email': df_canal['EMAIL_FINAL'].values,
            'RUT': df_canal['RUT_FINAL'].values
        })

        guardar_csv_formato_especial(df_export, ruta_archivo)

        info_extra = []
        if ruts_con_ceros > 0:
            info_extra.append(f"{ruts_con_ceros} RUTs con ceros")
        if emails_con_copy > 0:
            info_extra.append(f"{emails_con_copy} emails con -copy")
        extra_str = f"  [{', '.join(info_extra)}]" if info_extra else ''

        print(f"  📄 {nombre_archivo} → {len(df_export)} registros  (Canal: {canal}){extra_str}")
        archivos_generados.append((nombre_archivo, len(df_export), canal))

    # ========================
    # RESUMEN FINAL
    # ========================
    print("\n" + "=" * 80)
    print("📋 RESUMEN")
    print("=" * 80)
    total_exportados = sum(c for _, c, _ in archivos_generados)
    print(f"\n  Total registros exportados : {total_exportados}")
    print(f"  Archivos generados         : {len(archivos_generados)}")
    print(f"\n  Archivos en: {resultado_dir}")
    print("\n" + "=" * 80)
    print("✅ Proceso completado")
    print("=" * 80)


if __name__ == "__main__":
    generar_carga_southbridge()
