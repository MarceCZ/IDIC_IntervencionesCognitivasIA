# Intervenciones Cognitivas Asistidas por IA: Impacto del Robot NAO en la Memoria de Trabajo de Adolescentes

## Requisitos previos recomendados

- `Python 2.7.16` (Compatible con el entorno del robot NAO)
- `Python >= 3.10 y < 3.13`
- Extensión `Live Server` de **Visual Studio Code**
- NAO V6
- LM Studio **(Opcional)**

`NOTA:` Para el proceso completo de instalación y configuración de dependencias del robot NAO, consulte la sección **[Tutorial de Instalación y configuración](#tutorial-de-instalación-y-configuración)**.

## Estructura de carpetas

- `PruebaConocimiento:`
Prueba aplicada **pre** y **post** intervención, orientada a medir el conocimiento de conceptos relacionados con inteligencia artificial.

- `Experimentacion_GC:`
Prueba del **Grupo de COntrol** mediante una actividad asistida por computadora.

- `Experimentacion_GE:`
Prueba del **Grupo Experimental** utilizando los robot NAO.

- `Digit_Span_task:`
Prueba cognitiva adicional basada en Digit Span, utilizada como instrumento complementario para la evaluación de la memoria de trabajo.

- `Experimentacion_GE_2:`
Variante del código `Experimentacion_GE` utilizada para la evaluación manual de respuestas clasificadas incorrectamente por la IA durante la actividad y permite detener la grabación del audio de respuestas.

### NOTA 
**face-api** se utiliza para la recolección de emociones en tiempo real durante las intervenciones cognitivas.  
Este componente es compartido por los siguientes módulos:
- `Experimentacion_GC`
- `Experimentacion_GE`
- `Experimentacion_GE_2`

## Tutorial de Instalación y configuración

[Guía de instalación completa](https://www.notion.so/Documentaci-n-robots-NAOv6-y-Pepper-2-9-2bd8d044147a80218e4cd1f1bdc51579?source=copy_link)

### Recomendaciones de configuraciones
- Ubicar la ruta donde está ubicado `Python 2.7.16`, una ruta común en Window es `C:\Python27\` y renombrar `python.exe` a `python2.exe` para diferenciarlo de Python 3.


`NOTA:` Verifique que cada versión de Python pueda ejecutarse de forma independiente desde la terminal, por ejemplo:  
  - `python2 --version`  
  - `python --version` o `python3 --version`
