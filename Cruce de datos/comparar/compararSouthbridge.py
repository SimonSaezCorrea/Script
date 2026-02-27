"""
Script para comparar datos entre el archivo de carga Pawer y el archivo Southbridge.

Logica de comparacion:
  - Ambos archivos contienen RUTs "canonicos" (con ceros a la derecha para duplicados)
    y emails canonicos (con sufijos -copy para duplicados).
  - Para hacer el match se normaliza a la "base":
      * RUT base   -> quitar ceros a la derecha del RUT canonico (sin puntos ni guiones)
      * Email base -> quitar sufijo -+copy del segmento local (antes del @)
      * Canal      -> parte antes del ";" en Extra Info del registro Southbridge
  - Se recorren los registros de Southbridge uno a uno y se consume el primer
    registro Pawer disponible con la misma clave (rut_base, email_base, canal).
  - Coincidencias        -> Excel con datos originales de ambos ficheros.
  - Solo en Southbridge  -> Excel de inconsistencias (en DB pero no en la carga).
  - Sobrantes en Carga   -> CSV de carga pendiente (registros no encontrados en DB).

Archivos esperados en carpeta `data/Southbridge`:
  - Pawer *.xlsx                  (carga enviada por la empresa socia)
  - Southbridge_users_*.xlsx      (nuestro registro en DB)
"""
from __future__ import annotations

import os
import re
import sys
from collections import defaultdict, deque
from datetime import datetime

import pandas as pd

# Agregar la carpeta padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.normalizers import combinar_rut_dv, normalizar_nombre

# -- Nombres de columnas -----------------------------------------------------
# Pawer (carga)
P_POLIZA       = 'N° Póliza'
P_NOMBRE       = 'Nombre propietario'
P_AP_PAT       = 'Apellido paterno propietario'
P_AP_MAT       = 'Apellido materno propietario'
P_RUT          = 'Rut propietario'
P_DV           = 'Propietario DV'
P_EMAIL        = 'Email propietario'
P_TELEFONO     = 'Teléfono propietario'
P_CANAL        = 'Canal'
P_ESTADO_POL   = 'Estado póliza'

# Southbridge (DB)
S_NOMBRE       = 'Nombre'
S_APELLIDO     = 'Apellido'
S_EMAIL        = 'Email'
S_RUT          = 'RUT'
S_ESTADO       = 'Estado'
S_FECHA        = 'Fecha de creación'
S_TELEFONO     = 'Teléfono'
S_EXTRA_INFO   = 'Extra Info'


# -- Helpers de normalizacion ------------------------------------------------

def _fmt_rut(rut_raw: object) -> str:
    """Quita puntos, guiones y espacios; devuelve mayusculas. Conserva ceros finales."""
    if rut_raw is None or (isinstance(rut_raw, float) and pd.isna(rut_raw)):
        return ''
    s = str(rut_raw).strip().replace('.', '').replace('-', '').replace(' ', '').upper()
    return s


def _rut_base(rut_canonico: str) -> str:
    """
    Quita los ceros anadidos a la derecha de un RUT canonico.
      '2064048090'  -> '206404809'
      '206404809'   -> '206404809'  (sin cambio)
      '20640480900' -> '206404809'
    """
    stripped = rut_canonico.rstrip('0')
    return stripped if stripped else rut_canonico


def _email_base(email_raw: object) -> str:
    """
    Normaliza email y quita sufijos -copy en cualquiera de sus dos formas:
      simon-copy@d.com       -> simon@d.com   (copia en segmento local)
      simon--copy@d.com      -> simon@d.com
      simon@d.com-copy       -> simon@d.com   (copia tras el dominio)
      simon@d.com--copy      -> simon@d.com
    """
    if email_raw is None or (isinstance(email_raw, float) and pd.isna(email_raw)):
        return ''
    email = str(email_raw).strip().lower()
    # Caso: sufijo -copy al final del string completo (p.ej. user@domain.com-copy)
    email = re.sub(r'(-+copy)+$', '', email)
    if '@' not in email:
        return email
    local, domain = email.rsplit('@', 1)
    # Caso: sufijo -copy en el segmento local (p.ej. user-copy@domain.com)
    local = re.sub(r'(-+copy)+$', '', local)
    return f'{local}@{domain}'


def _extraer_canal(extra_info: object) -> str:
    """
    Extrae el Canal del campo Extra Info con formato 'Canal;Poliza N'.
    Devuelve el texto antes del primer ';'.
    """
    if extra_info is None or (isinstance(extra_info, float) and pd.isna(extra_info)):
        return ''
    return str(extra_info).split(';')[0].strip()


def _clave_match(rut_canonico_fmt: str, email_raw: object, canal: str) -> tuple:
    """Clave de matching: (rut_base, email_base, canal)."""
    return (_rut_base(rut_canonico_fmt), _email_base(email_raw), canal.strip())


# -- Funcion principal --------------------------------------------------------

def comparar_southbridge():
    """
    Compara los registros entre el archivo de carga Pawer y el registro Southbridge (DB).

    Flujo:
      1. Itera registro a registro por la DB Southbridge.
      2. Normaliza cada registro (rut_base + email_base + canal) y busca el primer
         registro Pawer disponible con la misma clave.
      3. Coincidencia  -> Excel con datos originales de ambos ficheros.
      4. Solo en DB    -> Excel de inconsistencias.
      5. Sobrantes en Carga Pawer (no consumidos) -> CSV de carga pendiente.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir   = os.path.join(script_dir, 'data', 'Southbridge')

    if not os.path.exists(data_dir):
        print(f'Error: no existe la carpeta de datos: {data_dir}')
        return

    # -- Localizar archivos --------------------------------------------------
    archivo_carga = None
    archivo_db    = None

    for fn in os.listdir(data_dir):
        if fn.startswith('~$'):
            continue
        ruta = os.path.join(data_dir, fn)
        if 'Southbridge_users' in fn and fn.endswith('.xlsx'):
            archivo_db = ruta
        elif fn.endswith('.xlsx'):
            archivo_carga = ruta

    if not archivo_carga or not archivo_db:
        print('Error: No se encontraron todos los archivos necesarios')
        print(f'   Carga Pawer:       {archivo_carga is not None}')
        print(f'   Southbridge (DB):  {archivo_db    is not None}')
        return

    print('=' * 80)
    print('COMPARACION CARGA PAWER vs SOUTHBRIDGE DB')
    print('=' * 80)
    print(f'\nArchivo Carga Pawer:     {os.path.basename(archivo_carga)}')
    print(f'Archivo Southbridge DB:  {os.path.basename(archivo_db)}')

    # -- Leer archivos -------------------------------------------------------
    print('\nLeyendo archivos...')
    try:
        df_carga = pd.read_excel(archivo_carga)
        print('  OK Carga Pawer leida')
    except Exception as exc:
        print(f'  Error al leer el archivo de carga: {exc}')
        return

    try:
        df_db = pd.read_excel(archivo_db)
        print('  OK Southbridge DB leida')
    except Exception as exc:
        print(f'  Error al leer el archivo de DB: {exc}')
        return

    print(f'\nRegistros totales: Carga={len(df_carga)}, DB={len(df_db)}')

    # -- Filtrar aprobados en Carga ------------------------------------------
    if P_ESTADO_POL in df_carga.columns:
        df_carga[P_ESTADO_POL] = df_carga[P_ESTADO_POL].astype(str).str.upper().str.strip()
        antes = len(df_carga)
        df_carga = df_carga[df_carga[P_ESTADO_POL] == 'APROBADO'].copy()
        print(f'  - Carga (aprobados): {len(df_carga)} ({antes - len(df_carga)} omitidos)')

    # -- Filtrar activos en DB -----------------------------------------------
    if S_ESTADO in df_db.columns:
        df_db[S_ESTADO] = df_db[S_ESTADO].astype(str).str.upper().str.strip()
        antes = len(df_db)
        df_db = df_db[df_db[S_ESTADO].isin(['VERDADERO', 'TRUE', 'ACTIVO', '1'])].copy()
        print(f'  - DB (activos):      {len(df_db)} ({antes - len(df_db)} omitidos)')

    # -- Calcular RUT canonico para la Carga (num + DV sin formateo) ---------
    df_carga['_RUT_CANON'] = df_carga.apply(
        lambda r: _fmt_rut(combinar_rut_dv(r.get(P_RUT, ''), r.get(P_DV, ''))),
        axis=1
    )
    df_carga['_EMAIL_CANON'] = df_carga[P_EMAIL].apply(
        lambda v: str(v).strip().lower() if pd.notna(v) else ''
    )
    df_carga['_CANAL'] = df_carga[P_CANAL].astype(str).str.strip()
    df_carga = df_carga[df_carga['_RUT_CANON'] != ''].copy().reset_index(drop=True)

    # -- Calcular RUT canonico para la DB ------------------------------------
    df_db['_RUT_CANON'] = df_db[S_RUT].apply(lambda v: _fmt_rut(v) if pd.notna(v) else '')
    df_db['_EMAIL_CANON'] = df_db[S_EMAIL].apply(
        lambda v: str(v).strip().lower() if pd.notna(v) else ''
    )
    df_db['_CANAL'] = (
        df_db[S_EXTRA_INFO].apply(_extraer_canal)
        if S_EXTRA_INFO in df_db.columns
        else pd.Series([''] * len(df_db))
    )
    df_db = df_db[df_db['_RUT_CANON'] != ''].copy().reset_index(drop=True)

    print(f'\nRUTs validos: Carga={len(df_carga)}, DB={len(df_db)}')

    # -- Construir indice consumible de Carga (clave -> deque de indices) -----
    indice_carga: dict = defaultdict(deque)
    for idx, row in df_carga.iterrows():
        clave = _clave_match(row['_RUT_CANON'], row['_EMAIL_CANON'], row['_CANAL'])
        indice_carga[clave].append(idx)

    print('\nComparando registros...')

    indices_carga_consumidos: set = set()
    coincidencias: list = []
    solo_en_db:    list = []

    # -- Iterar DB Southbridge y consumir registros de Carga -----------------
    for _, row_db in df_db.iterrows():
        clave_db = _clave_match(row_db['_RUT_CANON'], row_db['_EMAIL_CANON'], row_db['_CANAL'])
        cola = indice_carga.get(clave_db)

        if cola:
            idx_pawer = cola.popleft()
            indices_carga_consumidos.add(idx_pawer)
            row_carga = df_carga.loc[idx_pawer]

            coincidencias.append({
                # Datos Southbridge DB (valores originales)
                'DB_RUT':          row_db.get(S_RUT,        ''),
                'DB_EMAIL':        row_db.get(S_EMAIL,      ''),
                'DB_NOMBRE':       row_db.get(S_NOMBRE,     ''),
                'DB_APELLIDO':     row_db.get(S_APELLIDO,   ''),
                'DB_ESTADO':       row_db.get(S_ESTADO,     ''),
                'DB_EXTRA_INFO':   row_db.get(S_EXTRA_INFO, ''),
                'DB_FECHA':        row_db.get(S_FECHA,      ''),
                'DB_TELEFONO':     row_db.get(S_TELEFONO,   ''),
                # Datos Carga Pawer (valores originales)
                'CARGA_POLIZA':    row_carga.get(P_POLIZA,    ''),
                'CARGA_NOMBRE':    row_carga.get(P_NOMBRE,    ''),
                'CARGA_AP_PAT':    row_carga.get(P_AP_PAT,    ''),
                'CARGA_AP_MAT':    row_carga.get(P_AP_MAT,    ''),
                'CARGA_RUT':       row_carga['_RUT_CANON'],
                'CARGA_EMAIL':     row_carga['_EMAIL_CANON'],
                'CARGA_CANAL':     row_carga.get(P_CANAL,     ''),
                'CARGA_TELEFONO':  row_carga.get(P_TELEFONO,  ''),
                # Clave de matching utilizada
                'CLAVE_RUT_BASE':   clave_db[0],
                'CLAVE_EMAIL_BASE': clave_db[1],
                'CANAL':            clave_db[2],
                'ESTADO':           'COINCIDENCIA',
            })
        else:
            solo_en_db.append({
                'DB_RUT':          row_db.get(S_RUT,        ''),
                'DB_EMAIL':        row_db.get(S_EMAIL,      ''),
                'DB_NOMBRE':       row_db.get(S_NOMBRE,     ''),
                'DB_APELLIDO':     row_db.get(S_APELLIDO,   ''),
                'DB_ESTADO':       row_db.get(S_ESTADO,     ''),
                'DB_EXTRA_INFO':   row_db.get(S_EXTRA_INFO, ''),
                'DB_FECHA':        row_db.get(S_FECHA,      ''),
                'DB_TELEFONO':     row_db.get(S_TELEFONO,   ''),
                'CLAVE_RUT_BASE':   clave_db[0],
                'CLAVE_EMAIL_BASE': clave_db[1],
                'CANAL':            clave_db[2],
                'ESTADO':           'SOLO_EN_DB',
                'OBSERVACION':      'Registro en DB sin correspondencia en archivo de carga',
            })

    # Registros de Carga no consumidos por ningun registro de DB
    indices_sobrantes = [i for i in df_carga.index if i not in indices_carga_consumidos]
    df_sobrantes = df_carga.loc[indices_sobrantes].copy()

    # -- Imprimir resumen -----------------------------------------------------
    print('\n' + '=' * 80)
    print('RESULTADOS')
    print('=' * 80)
    print(f'\n  Registros DB analizados       : {len(df_db)}')
    print(f'  Coincidencias (DB <-> Carga)  : {len(coincidencias)}')
    print(f'  Solo en DB (sin match)        : {len(solo_en_db)}')
    print(f'  Solo en Carga (sobrantes)     : {len(df_sobrantes)}')

    if coincidencias:
        canales_match = pd.Series([r['CANAL'] for r in coincidencias]).value_counts()
        print('\n  Coincidencias por canal:')
        for canal, cnt in canales_match.items():
            print(f'    [{canal}]: {cnt}')

    if solo_en_db:
        canales_db = pd.Series([r['CANAL'] for r in solo_en_db]).value_counts()
        print('\n  Solo en DB por canal:')
        for canal, cnt in canales_db.items():
            print(f'    [{canal}]: {cnt}')

    if len(df_sobrantes) > 0:
        canales_sob = df_sobrantes['_CANAL'].value_counts()
        print('\n  Sobrantes en Carga por canal:')
        for canal, cnt in canales_sob.items():
            print(f'    [{canal}]: {cnt}')

    # -- Guardar resultados ---------------------------------------------------
    resultado_dir = os.path.join(script_dir, 'resultado')
    os.makedirs(resultado_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Excel de coincidencias
    if coincidencias:
        df_coinc = pd.DataFrame(coincidencias)
        archivo_coinc = os.path.join(resultado_dir, f'southbridge_coincidencias_{timestamp}.xlsx')
        df_coinc.to_excel(archivo_coinc, index=False)
        print(f'\nCoincidencias guardadas: {os.path.basename(archivo_coinc)}  ({len(df_coinc)} registros)')
    else:
        print('\nSin coincidencias para guardar.')

    # Excel de inconsistencias (solo en DB)
    if solo_en_db:
        df_incons = pd.DataFrame(solo_en_db)
        archivo_incons = os.path.join(resultado_dir, f'southbridge_inconsistencias_{timestamp}.xlsx')
        df_incons.to_excel(archivo_incons, index=False)
        print(f'Inconsistencias guardadas: {os.path.basename(archivo_incons)}  ({len(df_incons)} registros)')
    else:
        print('Sin inconsistencias para guardar.')

    # CSV de sobrantes de Carga (registros Pawer no encontrados en la DB)
    if len(df_sobrantes) > 0:
        archivo_csv = os.path.join(resultado_dir, f'southbridge_sobrantes_carga_{timestamp}.csv')
        _guardar_csv_sobrantes(df_sobrantes, archivo_csv)
        print(f'Sobrantes de carga guardados: {os.path.basename(archivo_csv)}  ({len(df_sobrantes)} registros)')
    else:
        print('No quedaron registros sobrantes en la carga.')

    print('\n' + '=' * 80)
    print('Proceso completado')
    print('=' * 80)


# -- Guardar CSV de sobrantes ------------------------------------------------

def _guardar_csv_sobrantes(df: pd.DataFrame, archivo_salida: str) -> None:
    """
    Guarda los registros de Carga Pawer que no tuvieron coincidencia en DB.

    Formato de cada linea:
        "nombre, apellido, email, rut",
    """
    with open(archivo_salida, 'w', encoding='utf-8-sig') as f:
        for _, row in df.iterrows():
            nombre   = normalizar_nombre(str(row.get(P_NOMBRE, '') or ''))
            ap_pat   = normalizar_nombre(str(row.get(P_AP_PAT, '') or ''))
            ap_mat   = normalizar_nombre(str(row.get(P_AP_MAT, '') or ''))
            apellido = f'{ap_pat} {ap_mat}'.strip()
            email    = str(row.get(P_EMAIL, '') or '').strip()
            rut      = row['_RUT_CANON']
            linea    = f'{nombre}, {apellido}, {email}, {rut}'
            f.write(f'"{linea}",\n')


if __name__ == '__main__':
    comparar_southbridge()
