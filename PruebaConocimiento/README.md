## Requisitos

- Python `>= 3.10 y < 3.13`
- LM Studio con algún modelo. Ejemplo `gpt-oss-20b`

## Instalación y configuración

### 1. Instalar dependencias
Desde la carpeta `PruebaConocimiento`, ejecutar:

```bash
py -m pip install -r requirements.txt
```

o:

```bash
python3 -m pip install -r requirements.txt
```

### 2. Configurar el modelo de IA 
Abrir el archivo de `config.py` y definir los siguientes valores dependiendo del modelo de IA a utilizar:

- Para un modelo de LM local utilizando LM Studio (Configuración actual)

```bash
API_KEY = "" # http://XXX.XXX.XXX.XXX:1234/v1/chat/completions
```

- Para un modelo comercial (Ejemplo: Gemini)
1. Instalar dependencias si tiene librería `py -m pip install google-generativeai`
2. Configurar los siguientes valores
```bash
API_KEY = "TU_API_KEY_AQUI"  #generar de Google AI
```
y descomentar los codigos que dicen

```bash
# Desbloquear el codigo para utilizar Gemini
```

### 3. Ejecutar la aplicación principal

```bash
py main.py
```

o:

```bash
python3 main.py
```

## Resultados (salidas generadas)

Se guardan datos de las intervenciones y se generan archivos en la carpeta **`resultados/`** para su análisis posterior.

### Archivo generado

**Resumen final de la evaluación**
   - **Ruta:** `resultados/<DNI>.txt`
   - **Descripción:** archivo de texto que registra toda las respuestas del participante durante la prueba, incluyendo:
     - texto de cada pregunta
     - respuesta ingresada por el usuario
     - resultado de la evaluación por la IA(**Correcto / Incorrecto**)
     - puntaje total sobre la cantidad de preguntas obtenidas

> **Nota**  
> El `<DNI>` corresponde al valor ingresado por el usuario en la pantalla de **Datos del participante** (por ejemplo: `12345678`).  
>  
> El archivo se crea o sobrescribe (en caso de ingresar el mismo DNI) en cada nueva ejecución de la prueba.

