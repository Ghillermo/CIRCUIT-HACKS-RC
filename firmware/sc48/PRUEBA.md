# SC48 / Beta 3.37 = SC47.9 / Beta 3.36 + sonidos de partida del FM (pad 8) + curva de velocity (Advanced Setup, K1) + MIDI 1 / 2 dos veces = Preset + Note de Setup = teclado al arpegiador + arreglo del selector de samples

`firmware/sc48/circuittracks-4486-SC48.syx` — SHA-256 `5a59fed3cab41bd56f9e489ce4af4cd3a7753f594b705eb55ef8887fc91bef80`, marca `SC48`.
`firmware/b3.37/circuittracks-4486-B3.37.syx` — SHA-256 `2bdba08410d47aa8258dc6c09883a03125c1aa8aee527f21c4c805b65db37f63`, marca `B3.37` (**Beta 3.37**, el mismo código).

El usuario (2026-10-27): «los parches de FM de la fila superior suenan todos muy parecidos, reduce el número de sintes demasiado iguales y añade
sonidos más de tipo "instrumento" como starters (piano, pluck, cuerdas, vientos)» · «añade los parches nuevos en otra página (pad 8) y deja en 7
algos por defecto» · «añade un atajo en advanced setup en K1 para cambiar la curva de respuesta de los pads (con centro por defecto) al moverlo se
muestra número y se ilumina velocity». «SC47.10» se cortaría a «SC47.1»: SC48.

## Qué probar
1. **Sonidos de partida del FM:** MIDI 1, vista Preset, motor FM (un toque al pad 27, pad 24). El **pad 8** se ve blanco tenue.
   - **Mantén el pad 8:** los pads 9-24 son 16 sonidos (fila 2: piano, piano eléctrico, órgano, pluck, arpa, marimba, bajo, campana; fila 3:
     cuerdas, pad, flauta, clarinete, metales, bombo, caja, hi-hat), en el color de su familia (teclados blanco, pulsados violeta, bajo azul,
     campana verde azulado, cuerdas verde, vientos azul claro, percusión rojo). Pulsa uno: se carga entero (algoritmo, ratios, niveles,
     envolventes, feedback, ruido, release) y suena la tónica mientras lo mantienes; con Shift, sin sonar. El cargado se ve brillante.
   - Un toque al pad 8 abre la página FM (como el pad 7). **El pad 7 mantenido sigue enseñando los 16 algoritmos** (solo cambia el algoritmo).
   - Escuchar que suenen distintos y a su instrumento; los valores de cada uno están en `tools/fmeng.py` (`STARTERS`) por si hay que retocarlos.
2. **Curva de velocity:** enciende con Shift pulsado (Advanced Setup). Gira **K1**: los pads enseñan el número (verde a la derecha, rojo a la
   izquierda, blanco en el centro) y **Velocity se enciende** 1,5 s.
   - Derecha (+1 … +8) = más sensible: golpes suaves suenan más fuerte. Izquierda (−1 … −8) = más dura. Centro (0) = el original.
   - Sal de Advanced Setup (Play) y toca: la velocity sigue la curva en todas las vistas. Con la velocity fija (Shift + Velocity = 96) no cambia.
   - Apaga y enciende: la curva se conserva (va en los ajustes del aparato).
3. **MIDI 1 / MIDI 2 dos veces seguidas** (en menos de 0,4 s): su vista Preset, como el botón Preset. Una sola pulsación: como siempre. Con Shift,
   Clear o Duplicate pulsados, en Setup o con el editor de CC abierto, no. En la vista Preset de MIDI con el motor apagado, **el pad 27 se ve gris** (blanco
   tenue).
4. **Setup normal, botón Note** = teclado externo al arpegiador (antes el pad 22 de Advanced Setup): verde encendido, rojo tenue apagado; se conserva al
   apagar. En Advanced Setup el pad 22 ya no hace nada.
5. **Selector de samples (arreglo de la 3.36):** con el transporte parado, pon un flip en un paso vacío y vuelve a la vista Note: la nota añadida se ve
   **al momento** (antes solo al dar Play), y los pasos con nota y flip se ven en **melocotón** (los que solo tienen nota, en su color de siempre; un flip
   sin nota solo se ve en el selector).
6. **Note con el step-drummer** (MIDI 1 / 2, motor encendido, step-drummer encendido con el pad 30): Note → Note ampliada → step-drummer → Note. Sin
   step-drummer, o en Synth 1 / 2, Note hace lo de siempre.
7. **Secuenciador de efectos con huecos vacíos:** motor «secuenciador de efectos» con la fila inferior de Master FX sin asignar: los valores 1-5 tocan
   los efectos de arriba de su columna (pad 26 = Gater … pad 30 = pad 5), con sus knobs; el LED de cada par en el color de ese efecto.
8. **Crackling del FM con 4 notas o más (arreglo):** en el modo de voz poly, cada voz baja según cuántas suenan (1 nota igual que antes; 2 al 71 %,
   3 al 58 %, 4 al 50 %, 6 al 41 %). Toca acordes de 4-6 notas con un FM fuerte (órgano, metales, velocity alta): sin chasquidos. Con una nota, el
   mismo volumen que antes. También con el oscilador en poly.
9. **Escucha previa en el cue:** Mixer, página de panorama, Shift + knob a la derecha = modo cue. En la vista Preset de Synth 1 elige un patch (toque y
   Shift + toque): la escucha sale **solo por la salida derecha**. En la vista Preset de Drum 1, **Shift + sample**: suena solo por la derecha; un toque
   normal, por la mezcla. Con el patrón sonando, toca en vivo ese drum justo después de un Shift + sample: debe sonar en la mezcla (izquierda).
10. Lo demás, como la Beta 3.36.

## Verificación en emulación
- `emu_fmstart.py`: pad 8 tenue / brillante; los 16 sonidos con sus colores; cada pad carga los 16 valores de su sonido y suena la tónica (con Shift
  no); al soltar el pad 8 vuelven los patches; el pad 7 mantenido = los algoritmos, y elegir uno solo cambia el algoritmo.
- `emu_velcurve.py`: sin curva las velocities no cambian; K1 en Advanced Setup escribe el byte 2 del parámetro 5 (las dos copias) y pide el guardado;
  el número y Velocity; las velocities = `velcurve.curve(v, c)` (por ejemplo +3: 20 → 26, 64 → 76; −8: 20 → 3, 64 → 32, 100 → 78); en la vista
  Setup normal K1 no hace nada nuestro.
- `emu_midipre.py`: MIDI 1 una vez y otra 500 ms después = su vista de pista; dos veces en 150 ms = su Preset (MIDI 2 igual); con Shift nada; el pad 27 en
  `0x02` con el motor apagado y en su color con el oscilador.
- `emu_notearp.py`: Note en el Setup normal cambia el bit 2 de las banderas de gmdrum en las dos copias y pide el guardado; LED `0x74` / `0x55`; con Shift
  nada; en Advanced Setup el pad 22 no hace nada y está apagado.
- `emu_notecyc.py`: MIDI 1 sin step-drummer / con el motor apagado = lo de siempre (19 ↔ 24); con él: 19 → 24 → 18 (step-drummer en pantalla) → 19 y
  la bandera de abierto borrada; Synth 1 = lo de siempre.
- `emu_fsqdef.py`: un hueco vacío pedido = el efecto de arriba de su columna, sin cargar copia; un hueco asignado igual que antes; el valor al azar
  con todos vacíos = uno de los efectos por defecto; `c_slotcol` = su color (en SC47.9: nada y blanco tenue).
- `emu_polygain.py`: oscilador en poly, 1-4 notas = velocity × 1 / 0,71 / 0,58 / 0,5; al soltar una, las otras al nivel de tres; FM con seis
  notas × 0,41; el unísono con su escala de siempre. En el núcleo 0 emulado (estudio de la sesión) una voz FM moderada llega a 0,37 del fondo de
  escala, tres a 0,95 y desde cuatro la suma recortaba.
- `emu_cueprev.py`: modo cue, patch de Synth 1 (toque y Shift) = la escucha programada y la pista solo al cue (panorama 127, envíos 0); 0,9 s
  tras soltar, de vuelta; Drum 1: toque normal = la mezcla, Shift + pad = el note-on al cue; el golpe propio de la escucha deja el cue y el
  siguiente golpe del drum lo devuelve a la mezcla antes de sonar; modo apagado = como el original.
- `emu_smnote2.py`: tras el gesto del selector, en la vista Note sin Play: el paso en melocotón, uno con solo nota en `0x13`, uno con solo flip vacío.
