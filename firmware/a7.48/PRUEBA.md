# Alpha 7.48 — prueba

Alpha 7.48 = Alpha 7.47 + `tools/gmgrid.py`: **la cuadrícula de la página 2 de la vista de macros global se guarda con el proyecto** (filas 1-3 en los bytes 4..6 de los ajustes del patrón 8 de MIDI 1, fila 4 en el byte 6 de los del patrón 8 de MIDI 2; a cero en las 210 sesiones comprobadas).

1. Encender unos pads de la cuadrícula, guardar el proyecto, cargar otro (cuadrícula vacía si no tenía), volver a cargar el primero: la cuadrícula vuelve.
2. Apagar y encender: la cuadrícula del proyecto cargado vuelve.
3. Un proyecto de una beta antigua con reglas de cadena en el patrón 8 de MIDI 1 / 2 puede abrir con algún pad encendido: tocarlo lo apaga.

Emulación: `python tools/emu_gmgrid.py firmware/a7.48`.
