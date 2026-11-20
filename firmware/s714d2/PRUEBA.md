# S714D2 (marca `S714D2`) — diagnóstico, sin publicar

= S714D + `tools/sxpanel.py` (gestos del panel desde el PC por SysEx, comando `05`). Imagen `0x6fee8`.

**Para qué:** una prueba de estrés dentro del aparato (el usuario: «keep the stress test, focus on in-unit operations»): `tools/panelstress_dev.py` manda gestos al azar (pads, knobs, botones de pista y de vista, Octave, Shift / Clear / Duplicate / Record mantenidos, Play) por las entradas del controlador, como pulsaciones de verdad, mientras `patscan` vigila los patrones y la caja negra lo demás; para al congelarse un registro o si el aparato deja de contestar.

**Nunca pulsa** Preset, Scales, Save ni Projects. MIDI 1 / 2 dos veces abre su vista Preset (huecos de patches propios): hazlo con un proyecto del **pack interno** (el primero; el mod no escribe en él).

## Probar
1. Cargar un proyecto del pack interno (o una copia de la tarjeta).
2. `python tools/panelstress_dev.py 600 12` (10 min, 12 gestos por segundo).
3. Si para con un registro: no apagar; `python tools/bbread.py --firmware S714D2`.

Pruebas `emu_sxpanel.py`, `emu_patscan.py`.
