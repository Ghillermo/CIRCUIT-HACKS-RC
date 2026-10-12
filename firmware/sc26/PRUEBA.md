# SC26 — SC25 + step-drummer en las pistas MIDI

`circuittracks-4486-SC26.syx` — SHA-256 en `manifest.json` (`syx_sha256`)
Marca `SC26`. Reserva: **SC25** (probada por el usuario: funciona). Todo probado en emulación; **nada probado en el aparato**.
RAM: **sin cambios** (el estado usa bytes que ya existían: ver «Cómo está hecho»). El estado guardado de SC24 / SC25 se conserva.

El step-drummer es un modo de secuenciación por pares de pasos, inspirado en otros sintetizadores percusivos por pasos, montado sobre el patrón de stock de la pista: no añade un secuenciador nuevo, edita las notas y un carril de automatización del patrón que ya existe.

**Alcance de esta build:** MIDI 1 y MIDI 2 con el modo VCA-VCF / OSC encendido (pad 27). **Pendiente** (acordado): lo mismo en Synth 1 / 2 enrutando a sus 8 macros, y el motor **VA-drum** (variante del oscilador con tres envolventes de decay, ruido y destinos de velocity).

## Cómo se usa
En la vista **Preset** de MIDI 1 / 2, con el pad 27 encendido:

| Control | Función |
|---|---|
| **Pad 30** | Abre / cierra la vista del step-drummer. Brillante = vista abierta; tenue = activado con la vista cerrada (los knobs vuelven a ser los del modo, el secuenciador sigue aplicando la fila de pitch); apagado = desactivado. **Shift + pad 30** = desactivar. |
| **Pads 1-16** | Los 16 pasos de la mitad que se muestra. Dos colores alternos por pares (1-2, 3-4, …); brillante = hay nota, tenue = vacío, **blanco** = el paso que suena. **Tocar** = escuchar ese paso (con su pitch); **Shift + tocar** = poner / quitar la nota del paso. |
| **Pads 17-24** | **Destino de la fila de pitch** (uno encendido): 17 tono de los dos osciladores · 18 tono solo del OSC 2 · 19 WAVE · 20 FM · 21 MIX · 22 env → filtro · 23 SHAPE · 24 DEC. |
| **Los 8 knobs** | Los 8 pares de pasos. Página **pitch**: el valor del par (0-127, **64 = sin cambio**); el LED lleva el color del destino. Página **velocity**: la velocity de las notas del par (**0 = sin nota**: se quita; al subir desde 0 se crea una nota en el primer paso del par); el LED lleva el color de la pista. |
| **Octave ▲ / ▼** | Página pitch / página velocity. |
| **1-16 / 17-32** | La otra mitad del patrón (pasos 17-32). |
| Pads 25-29 | Como siempre (editor de CC, patch flip, pad 27, 28, 29). |

- **Qué hace la fila de pitch.** Mientras el step-drummer está activado, el valor del par es un **desplazamiento** que se suma al destino cuando ese valor va al DSP; el knob de las páginas normales sigue siendo la base. En los dos destinos de tono: **±12 semitonos** continuos (64 = 0; un paso del knob ≈ 0,19 semitonos, repartido entre TUNE y FINE). En los demás: ±64 pasos del parámetro, con tope en sus límites.
- **Las notas.** Al abrir la vista (y al editar) todas las notas del patrón pasan a ser la **tónica de la escala en la octava 2** (nota MIDI 48 + tónica de la vista Scales), una sola nota por paso; se conservan la posición, la duración y la velocity de la primera nota de cada paso. **Es destructivo**: los acordes y las alturas del patrón se pierden.
- **Una nota nueva** (Shift + pad) toma la velocity de su par; si el par está vacío, la de la nota anterior más cercana (dando la vuelta al patrón); si no hay ninguna, 64. Dura un paso.
- **Qué patrón se edita:** el que la pista tiene seleccionado / está sonando.
- Con el step-drummer activado, el **carril 0** del patrón es la fila de pitch: ya no se lee como TUNE (lo de SC25) ni se graba al mover TUNE. Los otros 7 carriles de SC25 siguen igual.
- Se guarda con los ajustes: activado y destino, por pista. La vista arranca siempre cerrada, en la página de pitch y la primera mitad.

## Pruebas en el aparato (en este orden)
1. **Arranca**; Master FX y el modo VCA-VCF responden; **los valores guardados de SC25 siguen ahí**.
2. **Editor de CC** (pad 25): sigue funcionando (su vista ahora se deduce de la pista; antes guardaba un puntero).
3. MIDI 1, pad 27 en oscilador. **Pad 30**: se ilumina y aparecen los pasos en los pads 1-16 y los destinos en 17-24. Un patrón con notas: todas pasan a la tónica.
4. Página de pitch: gira K1…K8 y reproduce: cada par cambia el tono. Prueba otros destinos (pads 19-24).
5. **Lo que más importa oír:** el tono de cada paso debe estar ya en su sitio cuando empieza la nota (el valor se manda antes que la puerta). Si se oye un «chirrido» al inicio de cada nota, dímelo.
6. Octave ▼: velocity por par; a 0 el par calla; al subir vuelve la nota.
7. Tocar un pad de paso con el secuenciador parado: suena ese paso con su pitch; al soltar, calla. Shift + pad: pone / quita la nota.
8. Botón 1-16 / 17-32 con un patrón de 32 pasos.
9. Cambia de patrón con el step-drummer abierto: los knobs y los pads deben pasar al patrón nuevo (se lee el patrón de la pista en el motor del secuenciador; **sin confirmar en el aparato con el transporte parado**).
10. Pad 30 otra vez: la vista se cierra, la fila de páginas (pads 1-3) vuelve y los knobs son los del modo; la fila de pitch sigue sonando. Shift + pad 30: se desactiva y el tono vuelve al del knob.
11. Guarda el proyecto, apaga, enciende, carga: el patrón (notas y fila de pitch) y el estado activado / destino vuelven.

## Limitaciones conocidas
- Solo pistas MIDI con el modo encendido. Synth 1 / 2 y el motor VA-drum, en builds siguientes.
- La fila de velocity solo actúa sobre el nivel (lo que ya hace la velocity de la nota); sus otros destinos llegan con el motor VA-drum.
- El desplazamiento se recalcula cuando empieza una nota (o al tocar un par); un paso sin nota no cambia nada.
- Con dos osciladores, el tono del OSC 2 se actualiza por el barrido de valores volátiles (unos ms después que el del OSC 1).
- La nota audicionada también sale por MIDI (es una nota normal de la pista).

## Cómo está hecho (resumen; detalle en `docs/NOTAS.md`)
- Estado: un nibble por pista en `TAIL + 73` (bit 0 activado, bits 1-3 destino; los dos bytes `TAIL + 73 / 74` eran el puntero de vista del editor de CC, que ahora se deduce de su bit de pista), 3 bits del byte de flags (vista abierta, página, mitad), el byte 31 del bloque de Master FX (paso audicionado). Firma `0xB0` (un estado `0xAF` se conserva: solo se ponen a 0 esos dos bytes).
- Patrón: `[[0x2003C168 + 0x14 + 4 t] + 0x48] + 0xCA8 × patrón`; patrón y paso actuales = parámetros 0 / 1 del almacén `[0x20038ECC + 0x38 + 4 t]` del motor; paso = 28 bytes (máscara de notas, probabilidad, 6 unidades `nota, duración, micropaso, velocity`); carril 0 = `+0x3A8 + 6 × paso`.
- Desplazamiento: `c_sdfx` en el emisor del buzón del DSP (`c_vsend` y el barrido): lee el valor del carril en el paso que suena (o el audicionado) y devuelve valor + desplazamiento; los valores que mueve la fila de pitch se mandan antes que GATE / TRIG. Sin RAM para el desplazamiento.
- Imagen de 0x60A74 bytes. La DSP no cambia.

## Pruebas de emulación
`emu_sc26.py` (arranque con un estado de SC25, pad 30, la conversión de notas, los LEDs de pasos / destinos / knobs, las dos páginas de knobs, Shift + pad, la mitad, el desplazamiento en el buzón del DSP para tono / env → filtro / SHAPE / FM con sus topes, el orden antes de la puerta, la audición, la convivencia con los carriles de SC25, vista cerrada / desactivado, la segunda pista) y las de SC23.x / SC24 / SC25 sobre esta imagen.

## Si algo falla
Flashea SC25. Para volver al firmware original: el instalador, «RESTAURAR», o Novation Components.
