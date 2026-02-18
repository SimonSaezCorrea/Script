# Comparador ResPets

Script para comparar datos entre el archivo "Base Asegurados ResPets" y "ResPets_users".

## Archivos requeridos

Los archivos deben estar ubicados en la carpeta `data/Respets/`:

1. **Base Asegurados ResPets.xlsx**
   - Hoja "Activos": Usuarios que deberían estar activos
   - Hoja "Inactivos": Usuarios que deberían estar inactivos

2. **ResPets_users_[fecha].xlsx**
   - Base de datos actual de usuarios en el sistema

## Funcionamiento

### PASO 1: Procesar ALTAS (usuarios a agregar)

Compara la hoja "Activos" del archivo Base con los usuarios activos en ResPets_users.

**Características:**
- Identifica usuarios que están en la Base pero NO en ResPets_users
- **Manejo de duplicados**: Si un mismo RUT aparece múltiples veces en la Base:
  - Primera aparición: se usa el RUT original
  - Segunda aparición: se agrega un `0` al final del RUT
  - Tercera aparición: se agregan dos `00` al final del RUT
  - Y así sucesivamente...
  
  Ejemplo:
  ```
  RUT Original: 15377075
  Primera aparición: 15377075
  Segunda aparición: 153770750
  Tercera aparición: 1537707500
  ```

- **Emails únicos**: Para evitar duplicados de email:
  - Primera aparición: email original
  - Segunda aparición: agrega `-copy` (ejemplo: `email-copy@domain.com`)
  - Tercera aparición: agrega `--copy` (ejemplo: `email--copy@domain.com`)
  - Y así sucesivamente...

**Resultado:**
- Archivo CSV: `altas_respets_activacion_[timestamp].csv`
- Formato: Nombre, Apellido, Email, RUT

### PASO 2: Detectar usuarios activos que NO están en Base Activos

Identifica usuarios que están activos en ResPets_users pero NO aparecen en la hoja "Activos" de la Base.

**Características:**
- Compara usuarios activos en ResPets_users contra la hoja "Activos"
- Detecta usuarios que deberían ser desactivados porque ya no están en la base actual

**Resultado:**
- Archivo CSV: `bajas_respets_no_en_base_[timestamp].csv`
- Formato: Solo RUT (un RUT por línea)

### PASO 3: Procesar BAJAS (usuarios en hoja Inactivos)

Compara la hoja "Inactivos" del archivo Base con ResPets_users.

**Características:**
- Identifica usuarios que están en "Inactivos" pero tienen Estado=`True` en ResPets_users
- **IMPORTANTE**: Si un RUT está en AMBAS hojas (Activos e Inactivos), **prevalece Activos** (se mantiene activo)
- Solo incluye usuarios que están únicamente en Inactivos

**Resultado:**
- Archivo CSV: `bajas_respets_desactivacion_[timestamp].csv` (solo si hay registros)
- Formato: Solo RUT (un RUT por línea)

## Ejecución

```bash
python compararRespets.py
```

## Archivos de salida

Los archivos generados se guardan en la carpeta `resultado/` con un timestamp:

- `altas_respets_activacion_YYYYMMDD_HHMMSS.csv`: Usuarios a agregar/activar
- `bajas_respets_no_en_base_YYYYMMDD_HHMMSS.csv`: Usuarios activos que no están en Base Activos (a desactivar)
- `bajas_respets_desactivacion_YYYYMMDD_HHMMSS.csv`: Usuarios en hoja Inactivos (solo si hay registros después de excluir duplicados con Activos)

## Notas importantes

1. El script normaliza los RUTs eliminando puntos, guiones y ceros a la izquierda para comparación
2. Los duplicados se procesan siguiendo el mismo patrón que en Mapfre
3. El estado en ResPets_users se evalúa como booleano (`True`/`False`)
4. Los RUTs con ceros agregados indican que son duplicados en el archivo Base
5. **Si un RUT está en AMBAS hojas** (Activos e Inactivos), prevalece la hoja Activos y el usuario se mantiene activo
6. El script muestra un resumen final con la cantidad total de usuarios que deberían estar activos vs los que están actualmente
