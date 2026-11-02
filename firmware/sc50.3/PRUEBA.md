# SC50.3 / Beta 5.6 = SC50.2 + octava forzada en el modo salto + pads 17 y 25 de mutate en blanco + número del factor más corto

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc50.3/circuittracks-4486-SC50.3.syx` | `79420236a62d85667fcef063b58e92f1604f043baed510ab152d5bde819a25e4` | `SC50.3` |
| `firmware/b5.6/circuittracks-4486-B5.6.syx` (**Beta 5.6**) | `88227652015090de2a50514cb3cf22906a832400a288f32d58c7d065dd7f6a15` | `B5.6` |

El usuario (2026-11-01): «Podemos forzar la octava en cuanto se entra en este modo para que sólo se muestren los 32 pasos y nada por encima o por debajo?»; «los pads de mutate 17 y 25 (desactivado) color blanco»; «El tiempo que se muestra el factor de multiplicación en pantalla, más corto (la mitad o menos)».

## Qué cambia
- **Modo salto** (`tools/jumpoct.py`): al apuntar, la octava de la pista pasa a los pasos 1-16 y solo se mueve entre esa y la de los pasos 17-32. Octave ▼ apagado en 1-16, Octave ▲ apagado en 17-32, los dos apagados en la Note ampliada.
- **Mutate** (`mutate39.use_white25`): pad 25 como pad 17: blanco brillante mientras está desactivado, blanco tenue con las dinámicas encendidas.
- **Factor** (`mutfac.use_short`): el número se ve 0,6 s (antes 1,5 s).
- **Pitch de drums** (`tools/semitab.py`, para hacer sitio): los 128 valores salen de una octava. Debajo del centro difieren como mucho en una unidad de la tabla anterior (hasta 1 cent en el extremo más grave); desde Pitch 40, menos de 0,1 cents.

## Qué probar
1. MIDI 1 con la octava movida varias veces. Fila de motores, pad 9: al apuntar, la vista Note enseña los pasos 1-16 aunque la octava estuviera en otro sitio.
2. Octave ▲: pasos 17-32 y Octave ▲ apagado; otra pulsación no hace nada. Octave ▼: pasos 1-16 y Octave ▼ apagado; otra pulsación no hace nada.
3. Note ampliada: los dos Octave apagados; pasos 1-32.
4. Deja de apuntar: Octave vuelve a moverse libremente.
5. Pattern Settings, pad 25, un paso con notas: pads 17 y 25 en blanco brillante con todo apagado. Elige un nivel: 17 tenue. Enciende dinámicas: 25 tenue, 26-28 verdes.
6. Octave con esa vista abierta: el número se ve poco más de medio segundo.
7. Drums: el pitch en toda su carrera suena como antes, sobre todo en los graves; los cents también.

## Pruebas en emulación
`emu_jumpseq.py`, `emu_mutate2.py`, `emu_nudge2.py`, `emu_janko3.py`, `emu_sc50_2.py` (SC50.3 y B5.6) y las vecinas sobre SC50.3; `verify_builds.py`.

**Guía, lista de funciones y CHANGELOG no llevan aún nada posterior a la Beta 5.4:** se actualizan al publicar (factor 0,6 s, pad 25 blanco, octava forzada).
