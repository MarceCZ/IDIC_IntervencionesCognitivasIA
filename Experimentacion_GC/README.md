## Requisitos

- Python `>= 3.10 y < 3.13`
- Extensión `Live Server` de **Visual Studio Code**

## Instalación y configuración

### 1. Instalar dependencias
Desde la carpeta `Experimentacion_GC`, ejecutar:

```bash
py -m pip install -r requirements.txt
```

o:

```bash
python3 -m pip install -r requirements.txt
```

### 2. Configurar el modelo de IA (Gemini)
Abrir el archivo de `config.py` y definir los siguientes valores:

```bash
API_KEY = "TU_API_KEY_AQUI"     #generar de Google AI
MODEL = "gemini-2.5-pro"    #ejemplo
```

### 3. Ejecutar la aplicación principal

```bash
py main.py
```

o:

```bash
python3 main.py
```

### 4. Iniciar face-api.js
1. Abrir en una nueva ventana de VSCode la carpeta `faceapi`
2. Seleccionar y abrir `index.html`
3. Ubicar y clic en `Go Live` o click derecho sobre `index.html` y seleccionar `Open with Live Server`

## Resultados (salidas generadas)

Se guardan datos de las intervenciones y se generan archivos en la carpeta **`resultados/`** para su análisis posterior.

### Archivos generados

1. **Registro temporal (timeline) de la intervención**
   - **Ruta:** `resultados/registro_<ID>_timeline.txt`
   - **Descripción:** registra eventos y marcas de tiempo del flujo experimental (inicio, temas, fases) por cada pregunta:
     - tipo (Concepto / Ejemplo)
     - número de intento
     - resultado (Correcto / Incorrecto)
     - duración de respuesta (segundos)

2. **Resumen de puntuaciones por tema**
   - **Ruta:** `resultados/registro_sujeto<ID>_puntuaciones.txt`
   - **Descripción:** resumen final del desempeño del participante por tema:
     - si respondió correctamente la pregunta de **concepto**
     - si respondió correctamente el **ejemplo**
     - totales acumulados (conceptos correctos y ejemplos correctos)

3. **Registro de emociones en tiempo real (face-api.js)**
   - **Ruta:** `resultados/emociones_sujeto<ID>.csv`
   - **Descripción:** archivo CSV generado por el módulo web (face-api.js) con las emociones detectadas durante la intervención.
   - **Nota:** se guarda cuando finaliza la intervención y se envía la señal de cierre al navegador.

> **Nota**  
> El `<ID>` corresponde al DNI del usuario ingresado en la pantalla de **Datos del participante** (por ejemplo: `12345678`).

