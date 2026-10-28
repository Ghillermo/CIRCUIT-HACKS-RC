# SC48.3 / Beta 3.40 / RC2.11 / RC2.11S = SC48.2 / RC2.10 / RC2.10S + arreglo del editor de CC

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc48.3/circuittracks-4486-SC48.3.syx` | `06a98f4bfb4afd44f0b59f72e11d8788a52824635ca395ae3700a9fe9ad625ef` | `SC48.3` |
| `firmware/b3.40/circuittracks-4486-B3.40.syx` (**Beta 3.40**) | `90d0c45aa5ca09c7e35b48f1a8c04e234146dbfdf684514c607ef73296a523d9` | `B3.40` |
| `firmware/r211/circuittracks-4486-R211.syx` (**RC2.11**) | `0b514ad7fa332a15a9ab342790850b7711b5c27af5d0ce87c6992ccfd4fc1dff` | `R211` |
| `firmware/r211s/circuittracks-4486-R211S.syx` (**RC2.11S**) | `d5f751b80857c3ca959f2aac40fd838f2d494772d189de42dada8fa026f7d1c5` | `R211S` |

El usuario, en el aparato (2026-10-28): «knobs 4 and 5 update fine, but all the other knobs turned leds off and stopped working»; y «after hitting
save, the view must go back to default (exit to preset view)». La copia de deshacer del editor de CC estaba en una memoria que usan otras funciones:
al descartar un cambio la plantilla recibía sus bytes y los knobs quedaban muertos. Ahora tiene su propia memoria, y al guardar se sale del editor.

**Si los knobs ya están muertos:** apaga y enciende (vuelve la plantilla guardada), salvo que guardaras después; si guardaste, vuelve a enviar la
plantilla con Components.

## Qué probar
1. MIDI 1, vista Preset, una plantilla. Pad 25 (editor), gira K1 (elige), gira más (cambia el CC). **Sal con pad 25 sin guardar** (o un botón de
   vista): los 8 knobs con su LED y mandando sus CC de antes (monitor MIDI). Repetir con K3, K6, K8.
2. Pad 25, K1 a otro CC, **pad 26 (Save)**: el editor se cierra solo y estás en la vista Preset; K1 manda el CC nuevo, en la vista Preset, en la de
   pista y en la Note. Lo mismo guardando con Octave ▼ hasta el paso de guardar y Octave ▼ otra vez.
3. Apagar y encender: K1 sigue con el CC nuevo.
4. Con el editor abierto y cambios, usar cadenas de patrones, patches del sinte propio (Preset de MIDI 1 / 2), frecuencia de pasos: nada de eso se
   reinicia (antes la copia del editor pisaba su estado).

5. **Solo SC48.3 / Beta 3.40 — 128 patches del sinte propio:** vista Preset de MIDI 1 / 2, Octave ▼ siete veces = página 8 (Octave ▼ apagado,
   Octave ▲ encendido); Clear + pad dos veces guarda ahí; cargar, apagar / encender, volver a la página 8: sigue. En la vista Preset de Synth 1 / 2
   los patches de sinte del pack siguen igual (un hueco tras el final de un banco crea patches iniciales hasta él, como antes).
6. **Solo SC48.3 / Beta 3.40 — knobs no secuenciables:** vista Preset de MIDI 1 / 2 con el motor encendido. Con Shift, el pad 4 rosa tenue;
   **Shift + pad 4**: el pad 4 rosa y los knobs = Ataque, Decay, Sustain, SHAPE, LFO → filtro, Env → tono, MIX, Gain del VCA (suenan).
   **Shift + knob**: su destino (los LEDs en el color de la página del destino, los pads 9-24 enseñan dónde vive); suelta Shift y el knob mueve
   el nuevo. Con Record + Play, girar uno de estos **no graba** nada (salvo que su destino esté también en los knobs secuenciables). Clear
   mantenido, luego Shift + knob = el de fábrica. Guardar el patch, cargar otro, volver a cargarlo: los destinos vuelven. El pad 4 solo = la
   página 4 (knobs secuenciables) como siempre.
7. **Solo SC48.3 / Beta 3.40 — modificadores del arpegio:** Pattern Settings de Synth 1, Shift + pad 25 (arpegiador encendido): con Shift los
   pads 1-16 en cuatro grupos (cielo, cielo, ámbar, rosa; el elegido brillante). Probar con un acorde C E G: pad 2 (+1 octava) = C E G y luego una
   octava arriba; pad 6 (cada nota) = la octava cambia nota a nota; pad 10 (puntillo) = nota, nota larga; pad 11 (swing); pad 12 (dos veces);
   pad 14 (reinicio tras 1) = C E G C, C E G C… Con el arpegiador apagado, Shift + pad 4 = el primer paso de stock.
8. **Solo SC48.3 / Beta 3.40 — Nudge:** Pattern Settings, elige primer / último paso (p. ej. 6-13), pad 26 = el tramo pasa a 5-12 con sus
   notas; Shift + pad 26 = de vuelta a 6-13. Con el tramo en 1-…, pad 26 rota el patrón entero (lo del paso 1 al final). También en un drum.
9. **Solo SC48.3 / Beta 3.40 — latch:** con Shift en la vista Note las teclas ya no se ven amarillas / verdes. Fijar dos notas (Shift + pad), luego **Clear mantenido + el botón de la pista**: las dos dejan de sonar (y con el arpegiador encendido, el arpegio se para); un pad después suena normal.
10. **Solo SC48.3 / Beta 3.40 — dobles pulsaciones:** Scales, Scales otra vez = el editor de la escala propia, otra vez = fuera; en la vista Velocity, **Velocity otra vez** = velocity fija (como Shift + Velocity), otra vez = apagada; desde el Mixer, **Shift + Synth 1** = la vista de la fuente de Synth 1 (pads 25-30) y **Shift + MIDI 1** = la vista Preset de MIDI 1.
11. **Solo SC48.3 / Beta 3.40 — páginas de knobs mantenidas:** MIDI 1 con el motor encendido, vista Preset: tocar el pad 2 = la página se queda; **mantener el pad 4 un segundo** = la página de knobs secuenciables mientras lo mantienes, al soltar vuelve la anterior; igual con **Shift + pad 4** (knobs no secuenciables).

## Verificación en emulación
- `emu_edscratch.py` (por el controlador, con la tarea de LEDs y el servicio del DSP entre medias) frente a SC48.2 / RC2.10 / RC2.10S / Beta 3.39:
  la copia en `0x20046B00`; tras descartar, los 8 registros como antes y K1..K8 con su CC; Save = una escritura, el editor cerrado (vista Preset),
  K1 con el CC nuevo. Las builds anteriores enseñan el fallo (B3.38: solo K4 / K5 mandan; RC2.10: K1, K2, K4).
- `emu_mp128.py` (SC48.3 / Beta 3.40) frente a SC48.2: 8 páginas, los LEDs de Octave, el hueco 127 escrito en el banco 15, registro 7; SC48.2 con 4 páginas.
- `emu_nspage.py` (SC48.3 / Beta 3.40): Shift + pad 4 = la página 8 (pad 4 rosa; rosa tenue con Shift en la 4), K1 = Ataque sin grabar, Shift + K1 = el destino (lento, LEDs en color, la superposición), Clear + Shift + K1 = el de fábrica, los dos bloques del patch (+ 88 / + 130) guardados y restaurados; psave / xpatch con 142 bytes;
- `emu_arpmods.py`: las octavas (sin / +1 / +1 −1 / abajo), cuándo cambia (vuelta / cada nota / cada 4), dos veces, reinicio 1 y 3, puntillo y swing (los ticks), la entrada parada con puntillo (1,5 ×), los pads con y sin arpegiador; `emu_nudge2.py`: atrás / adelante / bordes en notas y drums; `emu_vmode`, `emu_fmeng2`, `emu_projsyn`, `emu_p4ovl`, `emu_smst`: bien.
