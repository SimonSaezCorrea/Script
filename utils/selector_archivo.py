import os
from pathlib import Path

def seleccionar_archivo(extensiones=None, titulo="SELECTOR DE ARCHIVOS"):
    """
    Interfaz de consola para navegar y seleccionar un archivo.
    
    Args:
        extensiones: Lista de extensiones permitidas (ej: ['.pdf', '.csv']). 
                    Si es None, muestra todos los archivos.
        titulo: Título personalizado para el selector.
    
    Returns:
        Ruta del archivo seleccionado o None si se cancela.
    """
    ruta_actual = Path.cwd()
    
    # Normalizar extensiones a minúsculas
    if extensiones:
        extensiones = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' for ext in extensiones]
    
    while True:
        # Limpiar pantalla (compatible con Windows y Unix)
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("=" * 60)
        print(titulo)
        print("=" * 60)
        print(f"\n📁 Ubicación actual: {ruta_actual}\n")
        
        # Listar contenido del directorio actual
        try:
            items = list(ruta_actual.iterdir())
            carpetas = sorted([item for item in items if item.is_dir()])
            
            # Filtrar archivos según extensiones
            if extensiones:
                archivos = sorted([
                    item for item in items 
                    if item.is_file() and item.suffix.lower() in extensiones
                ])
                ext_texto = ", ".join(extensiones)
            else:
                archivos = sorted([item for item in items if item.is_file()])
                ext_texto = "todos los tipos"
            
            # Mostrar opciones
            opciones = []
            tiene_parent = ruta_actual.parent != ruta_actual
            
            # Opción para subir un nivel (NO se agrega al array de opciones)
            if tiene_parent:
                print("0. ⬆️  [Subir un nivel]")
            
            # Listar carpetas
            idx = 1
            for carpeta in carpetas:
                print(f"{idx}. 📁 {carpeta.name}/")
                opciones.append(("dir", carpeta))
                idx += 1
            
            # Listar archivos
            if archivos:
                print(f"\n--- Archivos ({ext_texto}) ---")
                for archivo in archivos:
                    print(f"{idx}. 📄 {archivo.name}")
                    opciones.append(("file", archivo))
                    idx += 1
            else:
                print(f"\n⚠️  No hay archivos {ext_texto} en este directorio")
            
            # Opciones adicionales
            print(f"\n{idx}. ❌ Cancelar")
            opcion_cancelar = idx
            
            # Solicitar selección
            print("\n" + "=" * 60)
            try:
                seleccion = int(input("Selecciona una opción: "))
                
                if seleccion == 0 and tiene_parent:
                    ruta_actual = ruta_actual.parent
                elif seleccion == opcion_cancelar:
                    return None
                elif 1 <= seleccion < opcion_cancelar:
                    tipo, valor = opciones[seleccion - 1]
                    
                    if tipo == "dir":
                        ruta_actual = valor
                    elif tipo == "file":
                        return str(valor)
                else:
                    input("\n❌ Opción inválida. Presiona Enter para continuar...")
                    
            except ValueError:
                input("\n❌ Por favor ingresa un número válido. Presiona Enter para continuar...")
            except KeyboardInterrupt:
                return None
                
        except PermissionError:
            input(f"\n❌ Sin permisos para acceder a {ruta_actual}. Presiona Enter para volver...")
            ruta_actual = ruta_actual.parent
