# Scripts de Comparación - Carga vs BICE

Scripts para comparar datos entre archivos de carga y archivos BICE, detectando coincidencias, inconsistencias y diferencias de cantidad.

## Estructura de Carpetas

```
comparar/
├── data/
│   ├── Pyme/          # Archivos de BICE OMG Convenio y BICE PYME
│   ├── Sonda/         # Archivos de Sonda
│   ├── SII Group/     # Archivos de SII Group
│   └── Tinet/         # Archivos de Tinet
├── resultado/         # Archivos de salida (generados automáticamente)
├── compararPymeVsBice.py
├── compararSonda.py
├── compararSIIGroup.py
└── compararTinet.py
```

## Scripts Disponibles

### 1. compararPymeVsBice.py
Compara archivos de Pyme separando OMG y Pyme.

**Archivos esperados en `data/Pyme/`:**
- `*PAWER Asistencia de Mascotas*Pyme*.xlsx` (CARGA)
- `*BICE OMG Convenio*.xlsx` (BICE OMG)
- `*BICE PYME*.xlsx` (BICE PYME)

**Empresas OMG:**
- DDB CHILE SPA
- INFLUENCE & RESEARCH S.A.
- MEDIA INTERACTIVE S A
- OMD CHILE SPA
- OMNICOM MEDIA GROUP CHILE S.A.
- PHD CHILE S.A.

### 2. compararSonda.py
Compara archivos de Sonda.

**Archivos esperados en `data/Sonda/`:**
- `*Nomina*Sonda*.xlsx` (CARGA)
- `*Sonda_users*.xlsx` (BICE)

### 3. compararSIIGroup.py
Compara archivos de SII Group.

**Archivos esperados en `data/SII Group/`:**
- `*Nómina PAWER*SII Group*.xlsx` (CARGA)
- `*SII Group_users*.xlsx` (BICE)

### 4. compararTinet.py
Compara archivos de Tinet.

**Archivos esperados en `data/Tinet/`:**
- `*Base de datos Tinet*.xlsx` (CARGA)
- `*Tinet_users*.xlsx` (BICE)

## Funcionalidades

Todos los scripts incluyen:

✅ **Detección de coincidencias**: RUTs presentes en ambos archivos
⚠️ **Detección de inconsistencias**:
   - RUTs en Carga pero NO en BICE
   - RUTs en BICE pero NO en Carga
   - **🆕 Diferencias de cantidad**: RUTs que aparecen diferente número de veces en Carga vs BICE

## Archivos de Salida

Los resultados se guardan en `resultado/` con timestamp:

- `comparacion_coincidencias_YYYYMMDD_HHMMSS.xlsx` - Registros que coinciden
- `comparacion_inconsistencias_YYYYMMDD_HHMMSS.xlsx` - Registros con problemas

### Columnas en archivos de salida:
- `RUT` - RUT normalizado
- `ESTADO` - Tipo de resultado (COINCIDENCIA, DIFERENCIA_CANTIDAD, CARGA_SIN_BICE, etc.)
- `TIPO` - Tipo de registro (OMG, PYME, SONDA, etc.)
- `CANTIDAD_CARGA` - 🆕 Número de veces que aparece el RUT en Carga
- `CANTIDAD_BICE` - 🆕 Número de veces que aparece el RUT en BICE
- `OBSERVACION` - Descripción del resultado

## Ejemplo de Uso

```powershell
# Comparar Tinet
python '.\Cruce de datos\comparar\compararTinet.py'

# Comparar Pyme vs BICE
python '.\Cruce de datos\comparar\compararPymeVsBice.py'

# Comparar Sonda
python '.\Cruce de datos\comparar\compararSonda.py'

# Comparar SII Group
python '.\Cruce de datos\comparar\compararSIIGroup.py'
```

## Notas Importantes

1. Los scripts buscan archivos automáticamente por patrones en el nombre
2. Se filtran solo registros activos (Estado = VERDADERO) en archivos BICE
3. Los RUTs se normalizan (sin puntos, guiones, ni ceros extras)
4. 🆕 Se detectan diferencias cuando el mismo RUT aparece diferente número de veces
   - Ejemplo: 1 registro en Carga, 2 en BICE = DIFERENCIA_CANTIDAD

## Diferencias de Cantidad

Cuando un RUT aparece diferente número de veces en Carga vs BICE:

- **Estado**: `DIFERENCIA_CANTIDAD` (o `DIFERENCIA_CANTIDAD_OMG`/`DIFERENCIA_CANTIDAD_PYME`)
- **Observación**: "DIFERENCIA - Carga tiene X registros, BICE tiene Y registros"
- **Columnas adicionales**: `CANTIDAD_CARGA` y `CANTIDAD_BICE`

Esto ayuda a identificar duplicados o registros faltantes que comparten el mismo RUT.
