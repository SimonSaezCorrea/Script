from pypdf import PdfReader, PdfWriter
from pypdf.generic import DictionaryObject, ArrayObject, NameObject, NumberObject, TextStringObject, BooleanObject
import sys
from pathlib import Path

# Agregar el path para importar desde utils
sys.path.append(str(Path(__file__).parent.parent))
from utils.selector_archivo import seleccionar_archivo

def generar_nombre_salida(archivo_entrada):
    """
    Genera el nombre del archivo de salida removiendo '_Template' del nombre de entrada.
    """
    ruta = Path(archivo_entrada)
    nombre_sin_extension = ruta.stem
    
    # Remover '_Template' si existe
    if nombre_sin_extension.endswith('_Template'):
        nombre_sin_extension = nombre_sin_extension[:-9]  # Eliminar los últimos 9 caracteres ('_Template')
    
    # Retornar con la misma extensión
    return str(ruta.parent / f"{nombre_sin_extension}{ruta.suffix}")

def crear_plantilla_contrato(input_path, output_path, isBTC=False):
    reader = PdfReader(input_path)
    writer = PdfWriter()

    # Copiamos todas las páginas del original
    for page in reader.pages:
        writer.add_page(page)
    
    # Configuración base para los campos
    # Ajusta 'x' (horizontal) e 'y' (vertical) según tu PDF real.
    # Coordenadas: (0,0) es abajo-izquierda. A4 aprox es 595 x 842 puntos.
    
    # Ancho y alto estándar de las cajas de texto
    h_box = 12  # Altura de la caja
    font_size = 9  # Tamaño de fuente

    # Lista de campos requeridos por tu TypeScript
    # Estructura: (NombreCampo, Posición Y, Posición X)
    # Nota: Los valores de Y son estimados, tendrás que ajustarlos probando.
    campos = [
        # --- ANTECEDENTE DEL CONTRATANTE ---
        {"id": "fullname",      "y": 631.5,     "x": 110,   "w_box": 300}, # Nombre
        {"id": "identifier",    "y": 619.5,     "x": 92,    "w_box": 300}, # RUT
        {"id": "fulladdress",   "y": 607.5,     "x": 115,   "w_box": 300}, # Dirección
        {"id": "phone",         "y": 595,     "x": 113,   "w_box": 300}, # Teléfono ! 594.95 -> 595
        {"id": "email",         "y": 582.85,     "x": 151,   "w_box": 300}, # Correo ! 582.85
        
        # --- ANTECEDENTE DE LA MASCOTA ---
        {"id": "petname",       "y": 548.7,     "x": 110,   "w_box": 300}, # Nombre Mascota
        {"id": "specie",        "y": 536.1,     "x": 108,   "w_box": 300}, # Especie !
        {"id": "sex",           "y": 523.7,     "x": 97,    "w_box": 300}, # Sexo !
        {"id": "breed",         "y": 511.8,     "x": 97,    "w_box": 300}, # Raza
        {"id": "age",           "y": 499.9,     "x": 190,   "w_box": 300}, # Edad
        
        # --- VIGENCIA ---
        {"id": "startDate",     "y": 467.5,     "x": 160}, # Vigencia a contar de
    ]

    campos_BTC = [
        {"id": "price",         "y": 376,       "x": 219,   "w_box": 100}, # Banco
        {"id": "iva",           "y": 376,       "x": 322.5, "w_box": 50}, # Tipo de Cuenta
        {"id": "totalPrice",    "y": 376,       "x": 377,   "w_box": 160}, # Número de Cuenta
    ]

    # Crear el array de campos para el formulario
    fields = ArrayObject()
    
    # Iteramos y creamos cada campo
    for campo in campos:
        y_pos = campo["y"]
        x_pos = campo.get("x", 110)  # Default x si no está especificado
        w_box = campo.get("w_box", 300)  # Default width si no está especificado
        # Crear el campo de texto
        field = DictionaryObject()
        field.update({
            NameObject("/FT"): NameObject("/Tx"),  # Field Type: Text
            NameObject("/T"): TextStringObject(campo["id"]),  # Field Name (ID único)
            NameObject("/V"): TextStringObject(""),  # Value (vacío inicialmente)
            NameObject("/DV"): TextStringObject(""),  # Default Value
            NameObject("/DA"): TextStringObject(f"/Helv {font_size} Tf 0 0 0 rg"),  # Default Appearance (RGB negro)
            NameObject("/Ff"): NumberObject(0),  # Field flags
            NameObject("/Q"): NumberObject(0),  # Alineación (1=centro)
        })
        
        # Crear el widget annotation (la representación visual del campo)
        widget = DictionaryObject()
        widget.update({
            NameObject("/Type"): NameObject("/Annot"),
            NameObject("/Subtype"): NameObject("/Widget"),
            NameObject("/Rect"): ArrayObject([
                NumberObject(x_pos), 
                NumberObject(y_pos), 
                NumberObject(x_pos + w_box), 
                NumberObject(y_pos + h_box)
            ]),
            NameObject("/F"): NumberObject(4),  # Flag: Print
            NameObject("/P"): writer.pages[0].indirect_reference,
            NameObject("/MK"): DictionaryObject({
                NameObject("/BG"): ArrayObject([NumberObject(1), NumberObject(1), NumberObject(1)]),  # Fondo blanco
                NameObject("/BC"): ArrayObject([NumberObject(0), NumberObject(0), NumberObject(0)]),  # Borde negro
            }),
        })
        
        # Combinar el campo con su widget
        field.update(widget)
        
        # Agregar el campo al writer y obtener su referencia
        field_ref = writer._add_object(field)
        
        # Agregar el widget a la página
        if "/Annots" not in writer.pages[0]:
            writer.pages[0][NameObject("/Annots")] = ArrayObject()
        writer.pages[0]["/Annots"].append(field_ref)
        
        # Agregar el campo al array de campos del formulario
        fields.append(field_ref)

    # Si es BTC, agregar campos adicionales
    if isBTC:
        for campo in campos_BTC:
            y_pos = campo["y"]
            x_pos = campo.get("x", 110)
            w_box = campo.get("w_box", 300)
            
            # Crear el campo de texto
            field = DictionaryObject()
            field.update({
                NameObject("/FT"): NameObject("/Tx"),
                NameObject("/T"): TextStringObject(campo["id"]),
                NameObject("/V"): TextStringObject(""),
                NameObject("/DV"): TextStringObject(""),
                NameObject("/DA"): TextStringObject(f"/Helv {font_size} Tf 0 0 0 rg"),
                NameObject("/Ff"): NumberObject(0),
                NameObject("/Q"): NumberObject(1),
            })
            
            # Crear el widget annotation
            widget = DictionaryObject()
            widget.update({
                NameObject("/Type"): NameObject("/Annot"),
                NameObject("/Subtype"): NameObject("/Widget"),
                NameObject("/Rect"): ArrayObject([
                    NumberObject(x_pos), 
                    NumberObject(y_pos), 
                    NumberObject(x_pos + w_box), 
                    NumberObject(y_pos + h_box)
                ]),
                NameObject("/F"): NumberObject(4),
                NameObject("/P"): writer.pages[0].indirect_reference,
                NameObject("/MK"): DictionaryObject({
                    NameObject("/BG"): ArrayObject([NumberObject(1), NumberObject(1), NumberObject(1)]),
                    NameObject("/BC"): ArrayObject([NumberObject(0), NumberObject(0), NumberObject(0)]),
                }),
            })
            
            # Combinar el campo con su widget
            field.update(widget)
            
            # Agregar el campo al writer y obtener su referencia
            field_ref = writer._add_object(field)
            
            # Agregar el widget a la página
            if "/Annots" not in writer.pages[0]:
                writer.pages[0][NameObject("/Annots")] = ArrayObject()
            writer.pages[0]["/Annots"].append(field_ref)
            
            # Agregar el campo al array de campos del formulario
            fields.append(field_ref)

    # Crear el AcroForm (catálogo de formularios)
    acroform = DictionaryObject()
    acroform.update({
        NameObject("/Fields"): fields,
        NameObject("/NeedAppearances"): BooleanObject(True),  # Importante: Boolean, no String
        NameObject("/DR"): DictionaryObject({
            NameObject("/Font"): DictionaryObject({
                NameObject("/Helv"): DictionaryObject({
                    NameObject("/Type"): NameObject("/Font"),
                    NameObject("/Subtype"): NameObject("/Type1"),
                    NameObject("/BaseFont"): NameObject("/Helvetica"),
                })
            })
        })
    })
    
    writer._root_object[NameObject("/AcroForm")] = writer._add_object(acroform)

    with open(output_path, "wb") as f:
        writer.write(f)
    
    total_campos = len(campos) + (len(campos_BTC) if isBTC else 0)
    print(f"✅ Plantilla generada: {output_path}")
    print(f"   - {total_campos} campos de formulario creados")
    if isBTC:
        print(f"   - Campos estándar: {', '.join([c['id'] for c in campos])}")
        print(f"   - Campos BTC: {', '.join([c['id'] for c in campos_BTC])}")
    else:
        print(f"   - Campos: {', '.join([c['id'] for c in campos])}")

# --- Ejecutar ---
if __name__ == "__main__":
    print("🐾 Generador de Plantillas de Contrato PDF\n")
    
    # Seleccionar archivo de entrada mediante interfaz
    archivo_entrada = seleccionar_archivo(
        extensiones=['.pdf'],
        titulo="SELECTOR DE ARCHIVOS PDF"
    )
    
    if archivo_entrada is None:
        print("\n❌ Operación cancelada por el usuario.")
        exit(0)
    
    # Generar nombre de salida automáticamente
    archivo_salida = generar_nombre_salida(archivo_entrada)
    
    print("\n" + "=" * 60)
    print(f"📄 Archivo de entrada: {archivo_entrada}")
    print(f"📄 Archivo de salida:  {archivo_salida}")
    print("=" * 60 + "\n")
    
    # Preguntar si es BTC
    respuesta_btc = input("¿Es un contrato BTC? (true/false): ").strip().lower()
    isBTC = respuesta_btc in ['true', 't', 'verdadero', 'si', 'sí', 's', 'yes', 'y']
    
    if isBTC:
        print("✓ Se agregarán campos adicionales de BTC (price, iva, totalPrice)")
    else:
        print("✓ Se usarán solo los campos estándar")
    try:
        crear_plantilla_contrato(archivo_entrada, archivo_salida, isBTC)
    except FileNotFoundError:
        print(f"❌ No encontré el archivo: {archivo_entrada}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

