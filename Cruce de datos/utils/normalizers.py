"""
Funciones de utilidad para normalizar datos
"""
import re
import pandas as pd


def normalizar_rut(rut_str):
    """
    Normaliza un RUT eliminando puntos y guiones, dejando solo números y dígito verificador.
    
    Args:
        rut_str: String con el RUT en formato "12.345.678-9" o "12345678-9"
    
    Returns:
        String con RUT sin puntos ni guión: "123456789"
    """
    if not rut_str or str(rut_str).strip() == '':
        return ''
    
    # Convertir a string y limpiar espacios
    rut = str(rut_str).strip()
    
    # Eliminar puntos y guiones
    rut = rut.replace('.', '').replace('-', '')
    
    # Convertir a mayúsculas por si el dígito verificador es 'k'
    rut = rut.upper()
    
    return rut


def normalizar_email(email_str):
    """
    Normaliza un email convirtiéndolo a minúsculas y limpiando espacios.
    
    Args:
        email_str: String con el email
    
    Returns:
        String con email en minúsculas
    """
    if not email_str or str(email_str).strip() == '':
        return ''
    
    # Convertir a string, limpiar espacios y convertir a minúsculas
    email = str(email_str).strip().lower()
    
    return email


def combinar_apellidos(apellido_paterno, apellido_materno):
    """
    Combina apellido paterno y materno en un solo campo.
    
    Args:
        apellido_paterno: Apellido paterno
        apellido_materno: Apellido materno
    
    Returns:
        String con ambos apellidos separados por espacio
    """
    paterno = str(apellido_paterno).strip() if apellido_paterno else ''
    materno = str(apellido_materno).strip() if apellido_materno else ''
    
    if paterno and materno:
        return f"{paterno} {materno}"
    elif paterno:
        return paterno
    elif materno:
        return materno
    else:
        return ''


def combinar_rut_dv(rut, dv):
    """
    Combina RUT y dígito verificador en un solo string sin formato.
    
    Args:
        rut: Número de RUT
        dv: Dígito verificador (puede ser 0, K, etc.)
    
    Returns:
        String con RUT completo sin puntos ni guión: "123456789" o "12345678K"
    """
    # Verificar que el RUT no esté vacío
    if rut is None or str(rut).strip() == '':
        return ''
    
    # Convertir RUT a string y limpiar
    rut_str = str(rut).strip()
    
    # Si es un número flotante (ej: 20640480.0), convertir a entero primero
    if '.' in rut_str:
        try:
            rut_str = str(int(float(rut_str)))
        except:
            rut_str = rut_str.replace('.', '')
    
    # Eliminar guiones y puntos restantes
    rut_str = rut_str.replace('.', '').replace('-', '')
    
    # Procesar dígito verificador (importante: 0 es un DV válido)
    # Solo omitir si es None, NaN, o string vacío
    if dv is None or (isinstance(dv, float) and pd.isna(dv)) or str(dv).strip() == '':
        dv_str = ''
    else:
        dv_str = str(dv).strip().upper()
        
        # Si DV es un float (ej: 0.0 o 9.0), convertir a entero
        if '.' in dv_str:
            try:
                dv_str = str(int(float(dv_str)))
            except:
                dv_str = dv_str.replace('.', '')
    
    return f"{rut_str}{dv_str}"


def normalizar_nombre(nombre_str):
    """
    Normaliza un nombre convirtiéndolo a formato título (primera letra mayúscula, resto minúsculas).
    
    Args:
        nombre_str: String con el nombre
    
    Returns:
        String con nombre en formato título
    """
    if not nombre_str or str(nombre_str).strip() == '':
        return ''
    
    # Convertir a string, limpiar espacios y aplicar title case
    nombre = str(nombre_str).strip().title()
    
    return nombre
