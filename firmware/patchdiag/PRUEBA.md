# PATCHD («patchdiag») — DIAGNÓSTICO: ¿se conserva el relleno de los patches de sinte?

`circuittracks-4486-PATCHD.syx` — SHA-256 `d3cc136c4ade4dbff7a40807d5a789d4b3b8adc3c3c4d15e3b5ff13d3cc94b50`
Imagen de 0x66c80 bytes, CRC 0x31f57866, marca `PATCHD`. **No es un build de uso**: es SC38.9 + el diagnóstico remoto por USB (`rdiag`: leer / escribir ficheros de la SD y leer la memoria del DSP; sin borrar). Para volver: SC38.9.

## Para qué
Decidir si se pueden guardar **patches del sinte propio** (motor de MIDI 1 / 2) en los 172 bytes de relleno (`0xFF`) que hay detrás de cada patch de sinte en `Patches/NN_PATCHBANK.cpb`. Según el código del stock, sus dos maneras de guardar un patch no tocan ese relleno; esta prueba lo comprueba en el aparato.

## Qué necesitas
- **Un pack de prueba** (una copia de un pack): la prueba escribe en sus bancos de patches.
- Windows con Python, el Circuit Tracks por USB y nada más abierto que use sus puertos MIDI (Components, un DAW, monitores MIDI).
- `tools/ctremote.py` y `tools/padtest.py` del repositorio.

## Pasos
1. Envía PATCHD y carga el pack de prueba.
2. `python tools/ctremote.py ping` → versión `13800` (`$35E8`).
3. `python tools/padtest.py scan` → para cada banco (banco b = patches 8b+1 … 8b+8): tamaño, patches y si cada relleno es `F` (todo `0xFF`), `x` (otros datos) o `-` (el último patch, sin relleno). **Mándame el resultado.**
4. Elige un banco con 2-6 patches (pongamos el 0) y escribe las marcas:
   `python tools/padtest.py mark 0 --yes`
   - **A** en el relleno del primer patch (el caso normal);
   - **B** detrás del último patch (el fichero crece hasta completar el registro);
   - **C** en un registro nuevo tras el final: 340 bytes `0xFF` (un hueco vacío para el stock) y la marca.
5. `python tools/padtest.py check 0` → las tres `intact`.
6. **Aviso (2026-10-12):** el stock no guarda patches desde el panel (Save guarda el proyecto; las rutinas de guardado de patch solo se disparan por parámetro: Components). Los pasos 1-3 hay que hacerlos **desde Components**; el 4 y el 5, en el aparato.
   **En el aparato** (vista Preset de Synth 1), y tras cada paso, otra vez `check 0`:
   1. carga el primer patch del banco, cambia algo y **guárdalo en su mismo hueco** (A);
   2. comprueba que el hueco de C **se ve vacío**, guarda ahí un patch y que se cargue bien;
   3. guarda un patch **en un hueco posterior al final** del banco (por ejemplo, el patch 8 del banco);
   4. carga otro pack y vuelve al de prueba;
   5. apaga y enciende;
   6. (opcional) abre Components con el pack de prueba, haz una copia de seguridad o una sincronización y repite `check 0`.
7. Comprueba también que los patches del banco **siguen sonando igual** (las marcas solo están en el relleno).
8. Al acabar: `python tools/padtest.py unmark 0 --yes` (devuelve `0xFF`; el fichero se queda con el registro C vacío, que el stock ve como hueco vacío).

## Qué significa
- Todo `intact` tras los pasos del 6: el relleno es utilizable y se puede hacer el guardado de patches del sinte propio (ver «Estudio … patches del sinte propio» en `docs/NOTAS.md`).
- Una marca `changed` / `all 0xFF` / `gone` tras un paso concreto: ese paso pisa el relleno y habrá que esquivarlo (por ejemplo, reescribiendo tras ese guardado o evitando el último registro).

## Verificación en emulación
- `emu_sc35d8.py --dspx`: el diagnóstico por la ruta real del despachador de SysEx (`0x0801EB30`): ping, memoria, info / lectura / escritura con la API de stock.
- `emu_padtest.py`: `padtest.py` contra un modelo de la SD con el protocolo real y los dos guardados de stock tal como están en el código. Las marcas sobreviven a guardar en un hueco existente, guardar en el hueco vacío C y guardar tras el final.
