# SC27 — SC26 + step-drummer en Synth 1 / 2, LEDs del modo, knob del paso en blanco y dos páginas de knobs más

`circuittracks-4486-SC27.syx` — SHA-256 en `manifest.json` (`syx_sha256`)
Marca `SC27`. Reserva: **SC26** (probada por encima: «parece que funciona»). Todo probado en emulación; **nada probado en el aparato**.
RAM: **sin cambios**. DSP: sin cambios. El estado guardado de SC24 / SC25 / SC26 se conserva (misma firma `0xB0`).

## Qué cambia

### 1. Corrección: al cerrar el step-drummer se apagan las filas de pads
En SC26, al cerrar la vista (pad 30) o desactivar el modo (Shift + pad 30), los pads de los pasos 9-16 y de los destinos (pads 9-24) se quedaban encendidos. Ahora, con la vista cerrada, **los pads 9-24 quedan apagados**.

### 2. Botones iluminados dentro de la vista
Con la vista del step-drummer abierta:
- **Octave ▲** brillante = página de pitch; **Octave ▼** brillante = página de velocity (el otro, tenue).
- **1-16 / 17-32**: tenue = pasos 1-16, brillante = pasos 17-32.

Con la vista cerrada, esos tres LEDs son los de stock.

### 3. El knob del par que suena, en blanco
Mientras el secuenciador corre, el knob del par de pasos que está sonando se ve **blanco** (en las dos páginas, y solo si ese paso está en la mitad que se muestra).

### 4. Dos páginas de knobs más en el modo VCA-VCF / OSC de las pistas MIDI
La fila de páginas (pads 1-8 de la vista Preset, con el modo encendido) tiene ahora cinco pads. **Tocan los mismos valores; solo cambia la disposición.**

| Pad | Página | K1 | K2 | K3 | K4 | K5 | K6 | K7 | K8 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | VCA-VCF | (como antes) | | | | | | | |
| 2 | OSC 1 | (como antes) | | | | | | | |
| 3 | OSC 2 (solo con dos osciladores) | (como antes) | | | | | | | |
| **4** | **Secuenciables**: los 8 valores que el secuenciador automatiza, en el orden de sus carriles | TUNE | REL | ENVA | ENVF | FILT | RES | LRATE | FXAMT |
| **5** | **Modulación**: fila superior = envolvente, fila inferior = LFO | ATK | DEC | SUS | REL | LRATE | LFO→filtro | LFO→nivel | LFO→tono |
| 5 + Shift | cantidades | env→nivel | env→filtro | env→tono | env→forma | LFO→forma | LFO→morph | env→morph | — |

En la página 4, Shift + knob no hace nada.

### 5. Step-drummer en Synth 1 y Synth 2
- **Entrada:** pulsa el botón del sinte dos veces (la vista de la fuente de SC19.1, la de los cinco pads 25-29) y ahí **pad 30**. Brillante = vista abierta; tenue = cerrada. Otra pulsación la cierra. Cualquier botón Synth cierra la vista.
- **Pads 1-16:** los pasos (como en MIDI): tocar = escuchar el paso, Shift + tocar = poner / quitar la nota.
- **Pads 17-24:** **cuál de los 8 macros** escribe la fila de pitch (macro 1 … macro 8).
- **Los 8 knobs:** los 8 pares de pasos.
  - Página **pitch** (Octave ▲): el valor del macro elegido en ese par, como **posición absoluta** del macro (0-127), escrito en el carril de automatización de ese macro. Un par sin valor muestra (y parte de) la posición actual del macro. Lo reproduce el secuenciador de stock: es automatización normal del macro.
  - Página **velocity** (Octave ▼): la velocity de las notas del par (0 = sin nota), igual que en MIDI.
- **Octave ▲ / ▼** y **1-16 / 17-32**: como en MIDI.
- Los pads 25-29 (fuente del sinte) siguen funcionando con la vista abierta.

**Diferencias con las pistas MIDI:** en un sinte el valor es la posición del macro (no un desplazamiento sobre el knob) y lo que hace depende del parche (a qué está asignado ese macro). Para quitar la automatización de un macro: Clear + knob del macro en la vista normal del sinte, como siempre.

**Aviso (igual que en MIDI):** al abrir la vista y al editar, **todas las notas del patrón del sinte pasan a ser la tónica de la escala en la octava 2**, una por paso. Es destructivo: se pierden acordes y alturas. Úsalo con un patrón pensado para esto.

## Pruebas en el aparato (en este orden)
1. **Arranca**; los valores guardados siguen ahí.
2. MIDI 1, pad 27 en oscilador, **pad 30**: vista abierta; Octave ▲ brillante, ▼ tenue, 1-16/17-32 tenue. Octave ▼: se invierten. 1-16/17-32: brillante.
3. Play: el pad del paso y **el knob de su par** en blanco, avanzando.
4. **Pad 30 otra vez: los pads 9-24 se apagan** (la corrección). Shift + pad 30: siguen apagados.
5. Con la vista cerrada: **pad 4** → K1…K8 mueven TUNE, REL, env→nivel, env→filtro, FILT, RES, LRATE, FX. **Pad 5** → fila superior ATK DEC SUS REL, fila inferior LFO. Shift en la página 5: las cantidades.
6. Pads 1-3: las páginas de siempre.
7. **Synth 1:** botón dos veces → vista de la fuente → **pad 30**. Aparecen pasos y macros. Elige un macro que se oiga (pads 17-24), gira K1…K8 y pulsa Play: el macro cambia por pares.
8. Octave ▼: velocity por par. Tocar un pad de paso con el secuenciador parado: suena. Shift + pad: pone / quita la nota.
9. Pad 30: se cierra y los pads 1-24 se apagan. Preset: vuelve la vista de parches normal.
10. Vuelve a MIDI 1: sigue en la página de knobs donde la dejaste.

## Limitaciones conocidas
- La «vista abierta» es un solo estado para todas las pistas; al pulsar un botón Synth se cierra (en un sinte solo la abre el pad 30 de su vista de la fuente, para que la conversión de notas nunca sea una sorpresa).
- En los sintes la audición es una nota interna (no sale por MIDI); la nota audicionada usa el valor actual del macro, no el del paso (el carril solo se lee con el secuenciador en marcha).
- Los colores de los pads 4 / 5 y de los botones son provisionales (sin tabla RGB).

## Cómo está hecho (resumen; detalle en `docs/NOTAS.md`)
- Opciones `vcf21.use_sdrum2()` y `vcf21.use_pages5()`; builder `tools/build_sc27.py`.
- Sintes: ranuras 0 / 1 / 7 de la vista Preset del sinte (`0x0805AC9C`) → `c_sxpad` / `c_sxrel` / `c_sxleds`, delante de la vista de la fuente de SC19.1; los knobs por `c_vknob` / `c_vkleds` (los manejadores de macros de los sintes comparten vtable con los de MIDI): `c_sdsyn` reconoce el manejador de Synth 1 / 2 con su vista en pantalla. Carril = `+0x3A8 + 192 × macro + 6 × paso` del patrón del sinte; base = posición del macro (`0x08036192(sinte, 174 + 17 × macro)`); audición = `c_inject` de SC06.
- Estado: `TAIL + 74` = nibble por sinte (bits 1-3 el macro; el bit 0 es el tercer bit de la página de knobs de la pista MIDI del mismo índice). Sin RAM nueva.
- LEDs del panel: `c_sdpanel` al final de `c_vledtask` (LEDs 51 / 52 / 53).
- Imagen de 0x60DE4 bytes.

## Pruebas de emulación
`emu_sc27.py` (LEDs del panel, knob blanco, filas apagadas al cerrar, las dos páginas con cada knob, el bit de página por pista, la vista de los sintes: pad 30, conversión, macros, carril del macro, velocity, audición interna, pads de la fuente, cierre) y las de SC23.x / SC24 / SC25 / SC26 sobre esta imagen.

## Si algo falla
Flashea SC26. Para volver al firmware original: el instalador, «RESTAURAR», o Novation Components.
