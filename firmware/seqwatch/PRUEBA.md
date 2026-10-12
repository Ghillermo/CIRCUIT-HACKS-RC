# SEQWD («seqwatch») — DIAGNÓSTICO: ¿qué código lee las notas de un paso al reproducir?

`circuittracks-4486-SEQWD.syx` — SHA-256 `49f17a79534cb1c0836188563ec4a4b793eff31ab5191fa1257015525c50ec73`
Imagen de 0x66e30 bytes, CRC 0x1d06ed3f, marca `SEQWD`. **No es un build de uso**: es SC38.9 + el diagnóstico remoto por USB (`rdiag`) + un **punto de observación de datos** del procesador (DWT, la unidad de depuración del propio Cortex-M7) que se arma desde el PC. Para volver: SC38.9.

## Para qué
Para el random-mutate (fila 4 de la vista de probabilidad) hay que cambiar la nota de un paso justo antes de que suene. En emulación el secuenciador avanza los pasos pero nunca lee las notas: el código que las toca corre en una parte del firmware que la emulación no ejecuta. Este diagnóstico lo encuentra en el aparato: cuando algo lee el byte vigilado, el procesador salta a un manejador nuestro (DebugMonitor) que apunta la dirección del código que lo leyó.

## Qué necesitas
- Windows con Python, el Circuit Tracks por USB y nada más abierto que use sus puertos MIDI (Components, un DAW, monitores MIDI).
- `tools/ctremote.py` del repositorio. Lo manejo yo desde el PC si el aparato está conectado; los pasos son estos.

## Pasos
1. Envía SEQWD. Proyecto de prueba: en **Synth 1, patrón 1**, pon una nota en el **paso 1** (grabando o paso a paso).
2. `python tools/ctremote.py ping` → versión `13928` (`$3668`).
3. `python tools/ctremote.py step 0 0 0` → la dirección del paso 1 y sus bytes (máscara distinta de 0, la nota en la primera unidad).
4. **Referencia, parado:** `python tools/ctremote.py seqwatch 0 0 0` (vigila la nota del paso), espera unos segundos en la vista Note de Synth 1 **sin tocar nada**, y `python tools/ctremote.py wlog` → lo que lee la interfaz.
5. **Reproduciendo:** otra vez `seqwatch 0 0 0`, pulsa **Play** unos compases y `wlog` → las direcciones nuevas son las del reproductor.
6. (Opcional) Lo mismo con una pista MIDI (`seqwatch 2 0 0`, MIDI 1) y con **Record** encendido (el grabador escribe: `seqwatch 0 0 0 4 write`).
7. Al acabar: `python tools/ctremote.py watch 0 off`.

**No abras Master FX ni la vista Preset de MIDI 1 / 2 (editor de CC) durante la prueba**: el registro vive en el búfer de LEDs ocioso de Master FX y se borraría.

## Qué significa
- `wlog` da el número de lecturas y hasta 8 direcciones distintas de código (PC) con su LR (quién llamó). La dirección es la de unas instrucciones después de la lectura, dentro de la función que lee. Con eso localizo el reproductor en el listado y engancho ahí el random-mutate (sin notas colgadas: veré también cómo se apaga la nota).
- Si una lectura ocurre con las interrupciones enmascaradas, el aviso llega tarde y el PC apunta más adelante: por eso comparo la referencia parada con la reproducción.

## Verificación en emulación
- `emu_seqwatch.py`: `watch` / `poke` / `wlog` por la ruta real del despachador de SysEx (`0x0801EB30`) — DEMCR con TRCENA | MON_EN, DWT desbloqueado, COMP0 / MASK0 / FUNCTION0, el registro borrado — y el manejador con marcos de excepción hechos a mano (MSP y PSP): cuenta, 8 PC distintos con su LR, sin repetidos; DFSR y FUNCTION0. Unicorn no tiene DWT: la parte del aparato es la que se comprueba con este diagnóstico.
- `emu_sc35d8.py --dspx`: el resto de `rdiag` (ping, memoria, info / lectura / escritura).
