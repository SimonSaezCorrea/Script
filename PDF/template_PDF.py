from pypdf import PdfReader, PdfWriter
from pypdf.generic import DictionaryObject, ArrayObject, NameObject, NumberObject, TextStringObject, BooleanObject

def crear_plantilla_contrato(input_path, output_path):
    reader = PdfReader(input_path)
    writer = PdfWriter()

    # Copiamos todas las páginas del original
    for page in reader.pages:
        writer.add_page(page)
    
    # Configuración base para los campos
    # Ajusta 'x' (horizontal) e 'y' (vertical) según tu PDF real.
    # Coordenadas: (0,0) es abajo-izquierda. A4 aprox es 595 x 842 puntos.
    
    # Ancho y alto estándar de las cajas de texto
    w_box = 300
    h_box = 10  # Altura de la caja
    font_size = 9  # Tamaño de fuente

    # Lista de campos requeridos por tu TypeScript
    # Estructura: (NombreCampo, Posición Y, Posición X)
    # Nota: Los valores de Y son estimados, tendrás que ajustarlos probando.
    campos = [
        # --- ANTECEDENTE DEL CONTRATANTE ---
        {"id": "fullname",    "y": 632.5, "x": 110}, # Nombre
        {"id": "identifier",  "y": 620.5, "x": 92}, # RUT
        {"id": "fulladdress", "y": 608, "x": 115}, # Dirección
        {"id": "phone",       "y": 596, "x": 113}, # Teléfono
        {"id": "email",       "y": 583, "x": 151}, # Correo
        
        # --- ANTECEDENTE DE LA MASCOTA ---
        {"id": "petname",     "y": 549, "x": 110}, # Nombre Mascota
        {"id": "specie",      "y": 537, "x": 108}, # Especie
        {"id": "sex",         "y": 525, "x": 97}, # Sexo
        {"id": "breed",       "y": 512, "x": 97}, # Raza
        {"id": "age",         "y": 500, "x": 190}, # Edad
        
        # --- VIGENCIA ---
        {"id": "startDate",   "y": 468, "x": 160}, # Vigencia a contar de
    ]

    # Crear el array de campos para el formulario
    fields = ArrayObject()
    
    # Iteramos y creamos cada campo
    for campo in campos:
        y_pos = campo["y"]
        x_pos = campo.get("x", 110)  # Default x si no está especificado
        
        # Crear el campo de texto
        field = DictionaryObject()
        field.update({
            NameObject("/FT"): NameObject("/Tx"),  # Field Type: Text
            NameObject("/T"): TextStringObject(campo["id"]),  # Field Name (ID único)
            NameObject("/V"): TextStringObject(""),  # Value (vacío inicialmente)
            NameObject("/DV"): TextStringObject(""),  # Default Value
            NameObject("/DA"): TextStringObject(f"/Helv {font_size} Tf 0 0 0 rg"),  # Default Appearance (RGB negro)
            NameObject("/Ff"): NumberObject(0),  # Field flags
            NameObject("/Q"): NumberObject(0),  # Alineación (0=izquierda)
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
    
    print(f"✅ Plantilla generada: {output_path}")
    print(f"   - {len(campos)} campos de formulario creados")
    print(f"   - Campos: {', '.join([c['id'] for c in campos])}")

# --- Ejecutar ---
if __name__ == "__main__":
    # Asegúrate de que el nombre del archivo coincida con el que tienes en la carpeta
    archivo_entrada = "Contrato_Colaboradores_Roche_2026_Template.pdf" 
    archivo_salida = "Contrato_Colaboradores_Roche_2026.pdf"
    
    try:
        crear_plantilla_contrato(archivo_entrada, archivo_salida)
    except FileNotFoundError:
        print(f"❌ No encontré el archivo: {archivo_entrada}")
    except Exception as e:
        print(f"❌ Error: {e}")
