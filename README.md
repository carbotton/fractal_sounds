# FRACTAL SOUNDS

## Índice

- [1. Instalar Dependencias](#instalar-dependencias)
- [2. Configurar REAPER](#configurar-reaper)
  - [2.1 LoopMIDI](#loopmidi)
  - [2.2 Devices](#devices)
  - [2.3 Pistas](#pistas)
  - [2.4 Mensajes OSC](#mensajes-osc)
  - [2.5 Plugins](#plugins)

## Instalar dependencias
El archivo **requirements.txt** contiene las librerías necesarias para el funcionamiento del proyecto.

Posiblemente se tenga que instalar otras dependencias, como ser CUDA.

## Configurar REAPER

### LoopMIDI
Puerto MIDI virtual. 

Puede descargarse de: [loopMIDI | Tobias Erichsen (tobias-erichsen.de)](https://www.tobias-erichsen.de/software/loopmidi.html)

Este programa debe estar abierto para que REAPER pueda encontrar el puerto.

### Devices

Options > Preferences > MIDI Devices

Ingresar nombre del puerto MIDI y asegurarse de que esté marcado como "enabled". Debe coincidir con el que aparece en loopMIDI.

![captura_reaper_preferences.png](source%2Freadme%2Fcaptura_reaper_preferences.png)

### Pistas

Crear una pista por cada instrumento y una para la melodía generada por el usuario:

Estas pistas deben escuchar en el puerto MIDI virtual y deben ser configuradas con el canal correspondiente.

Para crear una nueva pista, click derecho sobre la sección recuadrada y seleccionar la opción "Insert new track":

![captura_reaper_agregar_pista_0.png](source%2Freadme%2Fcaptura_reaper_agregar_pista_0.png)
![captura_reaper_agregar_pista_1.png](source%2Freadme%2Fcaptura_reaper_agregar_pista_1.png)

Cuando aparezca la nueva pista, hacer click en el botón rojo de grabar. Luego hacer click en el botón "in" y seleccionar el canal correspondiente:

![captura_reaper_agregar_pista_2.png](source%2Freadme%2Fcaptura_reaper_agregar_pista_2.png)

![image](https://github.com/carbotton/tesis-ort/assets/89050568/87e8b20f-a6c0-4bd3-83d7-b294bcc6454e)

El listado de las pistas es como sigue:

1. Bajo 1
2. Batería 1
3. Melodía 1
4. Acordes 1
5. Notas de Fractal 1
6. Volumen General de Estilo 1
7. Volumen General de Estilo 2
8. Bajo 2
9. Batería 2
10. Melodía 2
11. Acordes 2
12. Notas de Fractal 2

Nótese que las pistas 6 y 7, son pistas master de cada grupo de pistas. Las pistas hijas deben ser ruteadas solamente hacia su correspondiente pista master, y no deben estar ruteadas directamente a la pista "MASTER" del DAW.

![image](https://github.com/carbotton/tesis-ort/assets/89050568/dccec288-4658-4a3e-9f0c-eef59038bb97)

![image](https://github.com/carbotton/tesis-ort/assets/89050568/5684b997-13a1-483f-ace3-a749ecdb1e2a)

Los canales a configurar son los que se muestran en el archivo config.py ubicado en la carpeta classes. Los canales en REAPER se numeran distinto, por lo tanto, si en el archivo de configuración el puerto indicado es el 2, en REAPER deberá seleccionarse el 3.

BASS_CHANNEL = 2  

DRUMS_CHANNEL = 9  

MELODY_CHANNEL = 3

CHORDS_CHANNEL = 4

FRACTAL_CHANNEL = 8

### Mensajes OSC

Options > Preferences > Control/OSC/Web

Click en "Add"

Ingresar datos como se muestra en la imagen.

![captura_reaper_osc.png](source%2Freadme%2Fcaptura_reaper_osc.png)

Los datos de IP y puerto deben ser actualizados en el archivo "player_config.py" ubicado en el proyecto dentro de la carpeta classes/player

### Plugins

Los plugins no pueden ser compartidos en el repositorio, la elección, descarga e instalación queda a cargo de los usuarios.

Los plugins de terceros que utilizados en la versión final de nuestro proyecto son: 

 - Kontak 7, con el instrumento "Hydra"
 - De Spitfire Audio, el instrumento "Soft Piano" y "Strings"
 - MT Power Drum Kit

Los demás plugins utilizados son nativo de REAPER, con la particularidad de que el el sampler para sonidos de bateria electrónica requiere que carguemos audios específicos que han sido seleccionados por nosotros. Estos audios sí están disponibles en nuestro repositorio en la carpeta "reaper", que además incluye el proyecto.

