# Beta 5.43 = Beta 5.42 (= SC55.7) + el mutate de patrones (de mefisme) + sitio en la flash

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/b5.43/circuittracks-4486-B5.43.syx` | `600139d1376ed8e9370c1b664936fc4abc98d750192c0a4c4e9f34f56696b5cd` | `B5.43` |

**Lo nuevo** (el usuario, 2026-11-10, desde la sesión de RYTHM: portar a Hacks el Pattern Mutate de mefisme con el diseño de RH86;
«Both» para el sitio, «Peach» para la página):
- **`tools/patmut.py`: el mutate de patrones** (de [Rhythm Plus de mefisme](https://github.com/mefisme/rhythm-plus), MIT, `modules/mutset.py`):
  en la vista Patterns (o el Mixer), **Shift + un toque a Duplicate** da a cada pista elegida una lista corta de patrones de su cadena en orden
  al azar, que suena en bucle en lugar de la cadena (los patrones no cambian). La lista sale de (semilla, pista, ajustes, cadena): cambiar un
  ajuste se nota al momento y volver a su valor devuelve la lista; cambiar la cadena sonando rehace la lista con la misma semilla.
  - **Shift + Duplicate mantenido 1/3 s en Patterns = la página de ajustes** (melocotón: el valor elegido brillante, los demás tenues):
    columna 1 Length 1-4, columna 2 Length 5-8, columna 3 tipo de longitud (como la cadena / exacta / al azar 1..Length), columna 4 Amount
    (todo / mucho / algo / poco: cuántos huecos de la cadena cambian), columna 5 Repeats (sí / no: dos vecinos nunca iguales), columna 6 Keep
    slot 1 (no / sí). Botones de pista brillantes = elegidas (con listas sonando, encender una = su lista, apagar = fuera). Duplicate cierra.
  - **Clear + Duplicate (en cualquier vista) = todas las listas terminan**; un pad de patrón de una pista termina la suya (y hace lo de stock).
  - Vista Patterns: en la columna de una pista con lista, los patrones que no están en ella apagados (el que suena, con su color). Con Shift,
    Duplicate amarillo en Patterns y en el Mixer. En las vistas de pista Shift + Duplicate sigue siendo lo de stock.
  - Con `patchain`: una pista con lista toca su lista, las demás siguen las reglas de cadena.
  - Guardado: el proyecto en la cola del registro + 367..375; **cada escena en sus bytes 34..39** (el guardado de escena del stock escribe el
  33): guardar una escena guarda pistas, semilla y ajustes; una escena que empieza (sonando) o se elige parado en el Mixer los devuelve; una
  escena sin ellos = sin listas.
- **`tools/tabpack.py`: sitio en la flash** (≈ 2,4 KB): cinco tablas de curvas (Master FX: PHPER, SMPI, GK, PHTAB; la FIX del FM) guardadas como
  segundas diferencias y 13 tablas del FM en un flujo LZ; se rehacen en la RAM (`0x20048620`) y la ITCM (`0x18A4`) cada vez que se envía el
  programa del núcleo 0 del DSP (al encender, antes de que nada las lea).

## Qué probar
1. Proyecto con cadenas de 2 a 4 patrones en varias pistas, sonando: vista Patterns, Shift + toque a Duplicate: cada pista toca sus patrones en
   otro orden; los que no están en la lista se apagan en su columna. Otro toque = otra lista.
2. Shift + Duplicate mantenido: la página melocotón; cambia Length / tipo / Amount / Repeats / Keep slot 1 y escucha que la lista cambia al
   momento; vuelve a un valor y debe volver la lista de antes. Apaga una pista con su botón: vuelve a su cadena. Duplicate cierra.
3. Clear + Duplicate en otra vista: todo vuelve a las cadenas. Un pad de patrón de una pista: esa pista vuelve a lo de stock.
4. Escenas: con listas sonando, guarda una escena; cambia de semilla; vuelve a la escena (sonando o parado desde el Mixer): debe volver la misma
   lista. Guarda el proyecto, apaga, carga: igual.
5. Lo de las tablas (sin cambios a la vista): Master FX (Phaser, sample capturado K1, Gater), el FM de 8 operadores (instrumentos, algoritmos
   del pad 7, importación de DX7) suenan como en la 5.42. **Instalar con el aparato frío (apagado y encendido) también**: las tablas se rehacen
   al arrancar.

## Verificación en emulación
- `emu_patmut.py` contra SC55.7: el generador del aparato = el modelo de `patmut.model` en 300 casos; el toque, la página y sus valores, la lista
  en el avance real `0x0802CB3C` (y la previsión igual), el apagado de la vista Patterns, Clear + Duplicate, el pad de patrón, la cadena nueva,
  la escena guardada / recuperada (sonando y parado), Shift + Duplicate en la vista de pista sin efecto; la build anterior no cambia nada.
- `emu_tabpack.py` contra SC55.7: `c_tboot` con la RAM / ITCM borradas rehace las 18 tablas byte a byte y llama a `c_dspz` con los mismos
  registros; las del FM iguales a las que SC55.7 tiene en la flash.
- `emu_examples.py`, `emu_fm8dest.py`, `emu_inst2.py`, `emu_fm8store.py`, `emu_gentab_mfx.py` pasan en SC55.8.
