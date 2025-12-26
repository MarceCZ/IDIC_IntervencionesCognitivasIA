## Requisitos

- Python `2.7.16`
- Python `>= 3.10 y < 3.13`
- Extensión `Live Server` de **Visual Studio Code**

## Instalación y configuración

### 1. Instalar dependencias
Desde la carpeta `Experimentacion_GE`, ejecutar:

- Para Python2

1. Instalar el [SDK de naoqi](../README.md#tutorial-de-instalación-y-configuración) (manual)  
2. Ejecutar los siguientes comandos
```bash
python2 -m pip install paramiko
python2 -m pip SimpleWebSocketServer
```

- Para Python 3

```bash
py -m pip install SpeechRecognition
```

o:

```bash
python3 -m pip install SpeechRecognition
```

### 2. Configurar el modelo de IA 
Abrir la carpeta `experimental`, ubicar el archivo y reeemplazar lo siguiente:

- Para un modelo de IA local utilizando LM Studio (Configuración actual) abrir el archivo `gpt_server.py`

```bash
API_KEY = "" # http://XXX.XXX.XXX.XXX:1234/v1/chat/completions
```

- Para un modelo comercial (Ejemplo: Gemini)
1. Instalar dependencias si tiene librería `py -m pip install google-generativeai`
2. Configurar los siguientes valores
```bash
API_KEY = "TU_API_KEY_AQUI"  #generar de Google AI
model_name = "gemini-2.5-flash" #Ejemplo
```

### 4. Iniciar face-api.js
1. Abrir en una nueva ventana de VSCode la carpeta `faceapi`
2. Seleccionar y abrir `index.html`
3. Ubicar y clic en `Go Live` o click derecho sobre `index.html` y seleccionar `Open with Live Server`

## Resultados (salidas generadas)

Se guardan datos de las intervenciones y se generan archivos en la carpeta **`resultados/`** para su análisis posterior.

### Archivos generados

1. **Resumen final de desempeño por sujeto**
   - **Ruta:** `resultados/registro_<ID>.txt`
   - **Descripción:** archivo de texto con el resumen final del desempeño del participante por cada tema:
     - resultado de **Concepto** (Correcto / Incorrecto)
     - resultado de **Ejemplo** (Correcto / Incorrecto)
     - totales acumulados:
       - número de conceptos correctos
       - número de ejemplos correctos

2. **Registro temporal (timeline) de la intervención**
   - **Ruta:** `resultados/registro_<ID>_timeline.txt`
   - **Descripción:** registro con marcas de tiempo (formato `MM:SS`) de los eventos ocurridos durante la sesión:
     - eventos detallados con marcas de tiempo inicio de forma todas las fases (observación / experimental)
     - inicio y fin de la **grabación del sujeto** (duración de respuesta)
     - resultado de cada evaluación (Concepto / Ejemplo)

3. **Registro de emociones en tiempo real (face-api.js)**
   - **Ruta:** `resultados/emociones_sujeto<ID>.csv`
   - **Descripción:** archivo CSV enviado desde el navegador vía WebSocket con las emociones detectadas durante la intervención.
   - **Nota:** se guarda cuando el script envía la señal de finalización (`FIN`) al navegador.

> **Nota**  
> El `<ID>` corresponde al DNI/número de sujeto ingresado en la ventana de **Datos del participante** (por ejemplo: `12345678`).
