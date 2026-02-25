"""
Script para comparar datos entre el archivo de carga Pawer y el archivo BICE Southbridge.

Compara RUTs y reporta inconsistencias.
La columna 'Canal' del archivo de carga se usa como extrainfo en el CSV de salida.

Archivos esperados en carpeta `data/Southbridge`:
- Pawer *.xlsx              (Carga Pawer - Altas a agregar, con columna Canal)
- Southbridge_users_*.xlsx  (BICE - Usuarios existentes)
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
from utils.normalizers import combinar_rut_dv, normalizar_nombre

# Constantes de columnas
NOMBRE_PROPIETARIO = 'Nombre propietario'
APELLIDO_PATERNO_PROPIETARIO = 'Apellido paterno propietario'
APELLIDO_MATERNO_PROPIETARIO = 'Apellido materno propietario'
EMAIL_PROPIETARIO = 'Email propietario'
COL_CANAL = 'Canal'
COL_EXTRA_INFO = 'Extra Info'  # Columna en el archivo BICE


def normalizar_ruts_dataframe_southbridge(df, col_rut, col_dv=None):
    """
    Normaliza RUTs en un DataFrame para comparación.
    Si tiene columna de DV separada, las combina primero.
    """
    if col_dv and col_dv in df.columns:
        df['RUT_COMPLETO'] = df.apply(
            lambda row: combinar_rut_dv(row.get(col_rut, ''), row.get(col_dv, '')), axis=1
        )
        col_a_normalizar = 'RUT_COMPLETO'
    else:
        col_a_normalizar = col_rut

    df['RUT_NORM'] = df[col_a_normalizar].apply(normalizar_rut_comparacion)

    # Filtrar solo RUTs válidos
    df = df[df['RUT_NORM'].notna() & (df['RUT_NORM'] != '')].copy()
    df['RUT'] = df['RUT_NORM']

    return df


def resolver_canal_por_rut(df_carga):
    """
    Para cada RUT único determina el/los canal(es) asociados.
    Si un RUT tiene varios canales distintos los concatena con ' | '.

    Returns:
        Serie indexada por RUT_NORM con el valor de Canal (str)
    """
    canal_por_rut = (
        df_carga.groupby('RUT_NORM')[COL_CANAL]
        .apply(lambda s: ' | '.join(sorted(s.dropna().astype(str).str.strip().unique())))
    )
    return canal_por_rut


def comparar_southbridge():
    """
    Compara los RUTs entre el archivo de carga Pawer y el archivo BICE de Southbridge.
    Incluye la columna Canal como extrainfo en los CSVs de salida.
    Gestiona correctamente los RUTs duplicados en el archivo de carga.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, 'data', 'Southbridge')

    archivo_carga = None
    archivo_bice = None

    if not os.path.exists(data_dir):
        print(f"❌ Error: no existe la carpeta de datos: {data_dir}")
        return

    for filename in os.listdir(data_dir):
        # Ignorar archivos temporales de Excel
        if filename.startswith('~$'):
            continue

        if 'Southbridge_users' in filename and filename.endswith('.xlsx'):
            archivo_bice = os.path.join(data_dir, filename)
        elif filename.endswith('.xlsx'):
            # Cualquier otro xlsx es el archivo de carga Pawer
            archivo_carga = os.path.join(data_dir, filename)

    if not archivo_carga or not archivo_bice:
        print("❌ Error: No se encontraron todos los archivos necesarios")
        print(f"   Carga Pawer:     {archivo_carga is not None}")
        print(f"   BICE Southbridge: {archivo_bice is not None}")
        return

    print("=" * 80)
    print("📊 COMPARACIÓN CARGA PAWER vs BICE - SOUTHBRIDGE")
    print("=" * 80)
    print(f"\nArchivo Carga Pawer: {os.path.basename(archivo_carga)}")
    print(f"Archivo BICE:        {os.path.basename(archivo_bice)}")

    # ── Leer archivos ────────────────────────────────────────────────────────
    print("\n🔄 Leyendo archivos...")

    try:
        df_carga = pd.read_excel(archivo_carga)
        print("  ✓ Archivo Carga Pawer leído correctamente")
    except Exception as e:
        print(f"  ❌ Error al leer archivo de carga: {e}")
        return

    try:
        df_bice = pd.read_excel(archivo_bice)
        print("  ✓ Archivo BICE leído correctamente")
    except Exception as e:
        print(f"  ❌ Error al leer archivo BICE: {e}")
        return

    print(f"\n📈 Registros totales:")
    print(f"  - Carga Pawer (total):  {len(df_carga)}")
    print(f"  - BICE (total):         {len(df_bice)}")

    # ── Filtrar solo aprobados en la carga ───────────────────────────────────
    total_carga = len(df_carga)
    if 'Estado póliza' in df_carga.columns:
        df_carga['Estado póliza'] = df_carga['Estado póliza'].astype(str).str.upper().str.strip()
        df_carga = df_carga[df_carga['Estado póliza'] == 'APROBADO'].copy()
        filtrados = total_carga - len(df_carga)
        print(f"  - Carga Pawer (aprobados): {len(df_carga)} ({filtrados} no aprobados filtrados)")

    # ── Filtrar activos en BICE ──────────────────────────────────────────────
    total_bice = len(df_bice)
    if 'Estado' in df_bice.columns:
        df_bice = filtrar_activos(df_bice, 'Estado')
        print(f"  - BICE (activos): {len(df_bice)} ({total_bice - len(df_bice)} inactivos filtrados)")

    # ── Procesar RUTs ────────────────────────────────────────────────────────
    print("\n🔧 Procesando RUTs...")

    df_carga = normalizar_ruts_dataframe_southbridge(df_carga, 'Rut propietario', 'Propietario DV')
    df_bice = normalizar_ruts_dataframe_southbridge(df_bice, 'RUT')

    print(f"  ✓ RUTs válidos: Carga={len(df_carga)}, BICE={len(df_bice)}")

    # ── Normalizar extrainfo del BICE ─────────────────────────────────────────
    if COL_EXTRA_INFO not in df_bice.columns:
        print(f"⚠️  Advertencia: el archivo BICE no tiene columna '{COL_EXTRA_INFO}'. La comparación será solo por RUT.")
        df_bice['EXTRA_INFO_NORM'] = ''
    else:
        # Normalizar: tomar solo la parte antes del ';' (ej. "Autoplanet;Poliza 2" → "Autoplanet")
        df_bice['EXTRA_INFO_NORM'] = (
            df_bice[COL_EXTRA_INFO].astype(str).str.strip()
            .str.split(';').str[0].str.strip()
        )

    df_carga['CANAL_NORM'] = df_carga[COL_CANAL].astype(str).str.strip()

    # Conteo de pares (RUT_NORM, Extra Info) en BICE
    bice_pair_counts = df_bice.groupby(['RUT_NORM', 'EXTRA_INFO_NORM']).size().to_dict()

    # ── Comparación fila a fila por (RUT, Canal) ─────────────────────────────
    df_carga = df_carga.reset_index(drop=True)
    # Rango de cada fila dentro de su grupo (RUT, Canal)
    df_carga['RANK_EN_CANAL'] = df_carga.groupby(['RUT_NORM', 'CANAL_NORM']).cumcount()
    # Cuántas ya están en BICE con ese mismo extrainfo
    df_carga['EN_BICE_COUNT'] = df_carga.apply(
        lambda r: bice_pair_counts.get((r['RUT_NORM'], r['CANAL_NORM']), 0), axis=1
    )
    # Una fila está cubierta si su rango < lo que ya hay en BICE para ese (RUT, Canal)
    df_carga['EN_BICE'] = df_carga['RANK_EN_CANAL'] < df_carga['EN_BICE_COUNT']

    df_filas_en_bice  = df_carga[df_carga['EN_BICE']]
    df_filas_sin_bice = df_carga[~df_carga['EN_BICE']]

    # ── Conteo inverso: entradas en BICE que NO tienen correspondencia en carga
    # Para cada (RUT, canal) en BICE, cuántas superan las de la carga
    carga_pair_counts = df_carga.groupby(['RUT_NORM', 'CANAL_NORM']).size().to_dict()
    bice_sin_carga_count = 0
    bice_sin_carga_detalle = {}  # canal → cantidad
    for (rut, canal), bice_cnt in bice_pair_counts.items():
        carga_cnt = carga_pair_counts.get((rut, canal), 0)
        extra = bice_cnt - carga_cnt
        if extra > 0:
            bice_sin_carga_count += extra
            bice_sin_carga_detalle[canal] = bice_sin_carga_detalle.get(canal, 0) + extra

    print(f"\n🔢 Cuadre general:")
    print(f"  ┌─ Carga Pawer    : {len(df_carga)}")
    print(f"  │    ✅ Ya en BICE : {len(df_filas_en_bice)}")
    print(f"  │    ⚠️  Sin BICE  : {len(df_filas_sin_bice)}")
    print(f"  └─ BICE (DB)      : {len(df_bice)}")
    print(f"       ✅ En carga   : {len(df_filas_en_bice)}")
    print(f"       ➕ Solo en DB  : {bice_sin_carga_count}  ← en DB pero no en la carga")
    if bice_sin_carga_detalle:
        for canal in sorted(bice_sin_carga_detalle):
            print(f"            [{canal}]: {bice_sin_carga_detalle[canal]}")
    print(f"  📐 Verificación: {len(df_filas_en_bice)} + {bice_sin_carga_count} = {len(df_filas_en_bice) + bice_sin_carga_count} (total DB: {len(df_bice)})")

    # Resumen por canal de los que faltan en BICE
    if len(df_filas_sin_bice) > 0:
        print(f"\n  📋 Faltantes por canal (a cargar):")
        for canal, cnt in df_filas_sin_bice['CANAL_NORM'].value_counts(dropna=False).items():
            ruts_canal = set(df_filas_sin_bice[df_filas_sin_bice['CANAL_NORM'] == canal]['RUT_NORM'])
            ya_en_bice_otro = sum(1 for r in ruts_canal if any(
                bice_pair_counts.get((r, ei), 0) > 0
                for ei in df_bice['EXTRA_INFO_NORM'].unique() if ei != canal
            ))
            nota = f" ({ya_en_bice_otro} RUTs ya en DB con otro extrainfo)" if ya_en_bice_otro > 0 else ''
            print(f"       [{canal}]: {cnt}{nota}")

    # ── Comparaciones (para Excel de resultados, por (RUT, Canal) único) ─────
    print("\n🔍 Realizando comparaciones...")

    print("\n" + "=" * 80)
    print("📊 RESULTADOS DE LA COMPARACIÓN")
    print("=" * 80)

    print(f"\n✅ Pólizas ya en BICE:  {len(df_filas_en_bice)} / {len(df_carga)}")
    print(f"⚠️  Pólizas sin BICE:   {len(df_filas_sin_bice)} / {len(df_carga)}")

    # ── Construir DataFrame de resultados (por par RUT + Canal) ─────────────
    resultados = []

    for (rut, canal), grp in df_carga.groupby(['RUT_NORM', 'CANAL_NORM']):
        carga_count = len(grp)
        bice_count  = bice_pair_counts.get((rut, canal), 0)
        reg_carga   = grp.iloc[0]

        nombre_carga  = normalizar_nombre(reg_carga.get(NOMBRE_PROPIETARIO, ''))
        apellido_pat  = normalizar_nombre(reg_carga.get(APELLIDO_PATERNO_PROPIETARIO, ''))
        apellido_mat  = normalizar_nombre(reg_carga.get(APELLIDO_MATERNO_PROPIETARIO, ''))
        apellidos_carga = f"{apellido_pat} {apellido_mat}".strip()

        bice_matches = df_bice[(df_bice['RUT_NORM'] == rut) & (df_bice['EXTRA_INFO_NORM'] == canal)]
        reg_bice = bice_matches.iloc[0] if len(bice_matches) > 0 else None

        # También revisar si el RUT está en BICE con OTRO extrainfo
        bice_otros = df_bice[(df_bice['RUT_NORM'] == rut) & (df_bice['EXTRA_INFO_NORM'] != canal)]
        extrainfo_en_bice = ', '.join(bice_otros['EXTRA_INFO_NORM'].unique()) if len(bice_otros) > 0 else ''

        if bice_count == 0 and len(bice_otros) > 0:
            estado = 'CARGA_SIN_BICE'
            observacion = f'FALTA [{canal}] - RUT existe en BICE pero con extrainfo: [{extrainfo_en_bice}]'
        elif bice_count == 0:
            estado = 'CARGA_SIN_BICE'
            observacion = f'FALTA - RUT en Carga [{canal}] pero NO en BICE con ese extrainfo'
        elif carga_count <= bice_count:
            estado = 'COINCIDENCIA'
            observacion = f'OK - {carga_count} póliza(s) ya en BICE para [{canal}]'
        else:
            # carga_count > bice_count pero bice_count > 0:
            # hay pólizas ya en BICE, las faltantes van al CSV → es una coincidencia parcial
            estado = 'COINCIDENCIA_PARCIAL'
            faltantes = carga_count - bice_count
            observacion = f'PARCIAL [{canal}] - {bice_count} póliza(s) ya en BICE, {faltantes} faltante(s) exportada(s) al CSV'

        resultados.append({
            'RUT': rut,
            'ESTADO': estado,
            'CANAL': canal,
            'NOMBRE_CARGA': nombre_carga,
            'APELLIDOS_CARGA': apellidos_carga,
            'NOMBRE_BICE': normalizar_nombre(reg_bice.get('Nombre', '')) if reg_bice is not None else '',
            'APELLIDO_BICE': normalizar_nombre(reg_bice.get('Apellido', '')) if reg_bice is not None else '',
            'EMAIL_CARGA': reg_carga.get(EMAIL_PROPIETARIO, ''),
            'EMAIL_BICE': reg_bice.get('Email', '') if reg_bice is not None else '',
            'CANTIDAD_POLIZAS_CARGA': carga_count,
            'CANTIDAD_BICE': bice_count,
            'EXTRAINFO_BICE_OTROS': extrainfo_en_bice,
            'OBSERVACION': observacion,
        })

    # ── Guardar resultados ───────────────────────────────────────────────────
    df_resultados = pd.DataFrame(resultados)

    orden_estados = {
        'COINCIDENCIA': 1,
        'COINCIDENCIA_PARCIAL': 1,  # Va al archivo de coincidencias, no inconsistencias
        'CARGA_SIN_BICE': 2,
    }

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    df_coincidencias, df_inconsistencias, archivos = separar_y_guardar_resultados(
        df_resultados, script_dir, timestamp, orden_estados, prefijo='southbridge_'
    )

    imprimir_resumen(df_coincidencias, df_inconsistencias, archivos)

    resultado_dir = os.path.join(script_dir, 'resultado')
    os.makedirs(resultado_dir, exist_ok=True)

    # ── Mapas de BICE para resolver slots y conflictos de email ─────────────
    # bice_email_slots[rut_norm] = {email_lower: slot_index}
    # Determina qué email ocupa qué slot (0 = RUT base, 1 = RUT+0, etc.)
    bice_email_slots = {}
    for _, row in df_bice.iterrows():
        rut = row['RUT_NORM']
        email = str(row.get('Email', '') or '').strip().lower()
        if not email:
            continue
        if rut not in bice_email_slots:
            bice_email_slots[rut] = {}
        if email not in bice_email_slots[rut]:
            bice_email_slots[rut][email] = len(bice_email_slots[rut])

    # bice_email_ruts[email] = set of rut_norms → para detectar conflictos cross-RUT
    bice_email_ruts = {}
    for _, row in df_bice.iterrows():
        email = str(row.get('Email', '') or '').strip().lower()
        rut = row['RUT_NORM']
        if not email:
            continue
        if email not in bice_email_ruts:
            bice_email_ruts[email] = set()
        bice_email_ruts[email].add(rut)

    # CSV por Canal: todas las filas de Carga que NO están en BICE (por póliza/fila)
    df_carga_filas_sin_bice = df_filas_sin_bice.copy()
    if len(df_carga_filas_sin_bice) > 0:
        canales = df_carga_filas_sin_bice[COL_CANAL].dropna().astype(str).str.strip().unique()
        for canal in sorted(canales):
            df_canal = df_carga_filas_sin_bice[
                df_carga_filas_sin_bice[COL_CANAL].astype(str).str.strip() == canal
            ].copy()
            if len(df_canal) == 0:
                continue

            df_canal = df_canal.reset_index(drop=True)
            df_canal['EMAIL_NORM'] = df_canal[EMAIL_PROPIETARIO].astype(str).str.strip().str.lower()

            # ── Asignar RANGO_EMAIL respetando los slots ya ocupados en BICE ──
            # Si el email ya existe en BICE para este RUT → usa ese slot (RUT sin ceros extra)
            # Si el email es nuevo para este RUT → slot siguiente al último de BICE
            new_email_slots = {}  # rut → {email_nuevo: slot_asignado}
            rangos = []
            for _, row in df_canal.iterrows():
                rut = row['RUT_NORM']
                email = row['EMAIL_NORM']
                slots_bice = bice_email_slots.get(rut, {})

                if email in slots_bice:
                    # Email ya registrado en BICE para este RUT → mantiene su slot
                    rangos.append(slots_bice[email])
                else:
                    # Email nuevo: asignar siguiente slot libre después de BICE
                    if rut not in new_email_slots:
                        new_email_slots[rut] = {}
                    if email not in new_email_slots[rut]:
                        next_slot = len(slots_bice) + len(new_email_slots[rut])
                        new_email_slots[rut][email] = next_slot
                    rangos.append(new_email_slots[rut][email])

            df_canal['RANGO_EMAIL'] = rangos
            df_canal['RUT_FINAL'] = df_canal.apply(
                lambda r: r['RUT_NORM'] + ('0' * r['RANGO_EMAIL']), axis=1
            )

            # ── Resolver conflictos de email con otros RUTs en BICE ──────────
            # Si el email ya lo usa OTRO RUT en BICE → agregar -copy
            emails_salida = []
            for _, row in df_canal.iterrows():
                rut = row['RUT_NORM']
                email = row['EMAIL_NORM']
                candidate = email
                while candidate in bice_email_ruts:
                    ruts_con_ese_email = bice_email_ruts[candidate]
                    if ruts_con_ese_email <= {rut}:
                        break  # Solo este RUT lo usa → sin conflicto
                    candidate = _agregar_copy(candidate)
                emails_salida.append(candidate)
            df_canal['EMAIL_FINAL'] = emails_salida

            ruts_con_ceros  = (df_canal['RANGO_EMAIL'] > 0).sum()
            emails_con_copy = sum(1 for o, f in zip(df_canal['EMAIL_NORM'], df_canal['EMAIL_FINAL']) if o != f)

            df_csv_canal = pd.DataFrame({
                'Nombre': df_canal[NOMBRE_PROPIETARIO].apply(normalizar_nombre),
                'Apellido': df_canal.apply(
                    lambda r: f"{normalizar_nombre(r.get(APELLIDO_PATERNO_PROPIETARIO, ''))} "
                              f"{normalizar_nombre(r.get(APELLIDO_MATERNO_PROPIETARIO, ''))}".strip(),
                    axis=1
                ),
                'Email': df_canal['EMAIL_FINAL'],
                'RUT': df_canal['RUT_FINAL'],
            })

            # Nombre de archivo limpio (sin espacios)
            canal_filename = canal.replace(' ', '_').replace('/', '-')
            archivo_csv_canal = os.path.join(
                resultado_dir, f'carga_sin_bice_{canal_filename}_{timestamp}.csv'
            )
            _guardar_csv_con_canal(df_csv_canal, archivo_csv_canal)
            info = []
            if ruts_con_ceros  > 0: info.append(f"{ruts_con_ceros} RUTs con ceros")
            if emails_con_copy > 0: info.append(f"{emails_con_copy} emails con -copy")
            extra_str = f"  [{', '.join(info)}]" if info else ''
            print(f"   📄 [{canal}] {len(df_csv_canal)} registros → {os.path.basename(archivo_csv_canal)}{extra_str}")

    # Muestra de inconsistencias
    if len(df_inconsistencias) > 0:
        print("\n🔍 Muestra de inconsistencias (primeros 10):")
        columnas_mostrar = ['RUT', 'ESTADO', 'CANAL', 'NOMBRE_CARGA', 'NOMBRE_BICE']
        print(df_inconsistencias.head(10)[columnas_mostrar].to_string(index=False))

    print("\n" + "=" * 80)
    print("✅ Proceso completado")
    print("=" * 80)




def _agregar_copy(email):
    """
    Añade o incrementa el sufijo -copy en un email:
      user@d.com → user-copy@d.com → user--copy@d.com → user---copy@d.com ...
    """
    if '@' in email:
        nombre, dominio = email.rsplit('@', 1)
        # Si ya termina en 'copy', inserta un guion extra antes de 'copy'
        if nombre.endswith('copy'):
            nombre = nombre[:-4] + '-copy'
        else:
            nombre = nombre + '-copy'
        return f"{nombre}@{dominio}"
    return f"{email}-copy"


def _guardar_csv_con_canal(df, archivo_salida):
    """
    Guarda el CSV de usuarios a agregar.
    Formato: "Nombre,Apellido,Email,RUT"
    """
    columnas = ['Nombre', 'Apellido', 'Email', 'RUT']
    with open(archivo_salida, 'w', encoding='utf-8-sig') as f:
        encabezado = ','.join(columnas)
        f.write(f'"{encabezado}",\n')
        for _, row in df.iterrows():
            valores = ','.join(str(row.get(c, '')) for c in columnas)
            f.write(f'"{valores}",\n')


if __name__ == "__main__":
    comparar_southbridge()
