# SC25 — SC24 + CC / NRPN de entrada y salida, automatización por el secuenciador y la fila de plantillas del pad 27

`circuittracks-4486-SC25.syx` — SHA-256 en `manifest.json` (`syx_sha256`)
Marca `SC25`. Reserva: **SC24** (si no arranca o se comporta raro: SC23.6, confirmado por el usuario). Todo probado en emulación; **nada probado en el aparato**.
RAM: **sin cambios** (la misma reserva que SC24: las tablas están en flash y el estado de los NRPN entrantes usa un registro que ya existe en stock).

## Qué cambia
1. **Corrección del pad 27.** Al apagar el modo (oscilador → apagado) la fila de plantillas (pads 1-8) vuelve a verse: mientras el modo está apagado y el editor de CC no dibuja, la vista Preset de MIDI 1 / 2 vuelve a pintar la fila de stock en cada fotograma.
2. **CC de salida.** Todo valor del modo que cambia un knob (también **Clear + knob**, que manda el valor por defecto) sale por MIDI en el canal de la pista, por el emisor de CC de las plantillas de stock: respeta el filtro **CC Tx** del Setup y el reenvío interno de SC05 (si MIDI 1 / 2 comparte canal con un sinte, el CC mueve también ese sinte). Los valores bipolares salen con +64 (0-127, 64 = centro).
3. **CC de entrada.** Los mismos CC / NRPN que llegan por el canal de una pista MIDI **con el modo encendido** ponen esos valores (el filtro **CC Rx** del Setup manda; las copias internas del reenvío de SC05 se ignoran; nada se devuelve por MIDI). No se guardan en los ajustes (solo los cambios hechos con los knobs, como antes).
4. **Automatización.** Ocho valores se graban y se reproducen con el secuenciador de stock por los carriles de macros de la pista (la misma pista de automatización que la de las macros de stock: ids 20 + k de MIDI 1 y 30 + k de MIDI 2).

## Tabla de CC y NRPN
Números de CC / NRPN del **sinte de stock** donde la función es la misma (o muy parecida) y NRPN **4:código** para el resto (el LSB es el código del valor; el MSB 4 no lo usa ningún parámetro de stock).

| Valor (knob) | Sale como | | Valor (knob) | Sale como |
|---|---|---|---|---|
| FILT (página VCA-VCF, K5) | CC 74 (bipolar) | | TUNE (página OSC1, K1) | CC 26 (bipolar) |
| RES (K6) | CC 71 | | FINE (Shift + K1) | CC 27 (bipolar) |
| ENVF, env → filtro (K4) | CC 79 (bipolar) | | WAVE (K7) | CC 20 |
| ATK (K1) | CC 73 | | SHAPE (K2) | CC 21 |
| DEC (Shift + K2) | CC 75 | | TUNE2 (página OSC2, K1) | CC 37 (bipolar) |
| SUS (Shift + K1) | CC 70 | | FINE2 (Shift + K1) | CC 39 (bipolar) |
| REL (K2) | CC 72 | | WAVE2 (K7) | CC 30 |
| FXAMT (K8) | CC 91 | | SHAPE2 (K2) | CC 31 |
| GAIN (Shift + K6) | CC 59 | | MIX (página OSC1, Shift + K2) | CC 52 |
| LRATE, velocidad del LFO (K7) | NRPN 0:76 (el del LFO 1 de stock) | | RING (página OSC2, Shift + K3) | CC 54 |
| LFOF, LFOV, FXTYPE, FTYPE, ENVA, LFOP, ENVP, ENVW, LFOW, ENVM, LFOM, BITSYNC, FM | NRPN 4:código (código = 4, 12, 13, 16, 15, 21, 22, 23, 24, 25, 26, 32, 33) | | | |

Un NRPN sale como CC 99 (MSB) – CC 98 (LSB) – CC 6 (valor de 7 bits). Mapa completo: `vcf21.CC_TAB`.

## Carriles de automatización
| Carril (macro) | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| Valor | **TUNE** | REL | ENVA (env → VCA) | ENVF (env → filtro) | FILT | RES | LRATE | FXAMT |

- Grabar: con el secuenciador grabando, mover uno de esos knobs graba su movimiento en el carril; lo demás (ATK, DEC, SUS, tipos, OSC2, MIX, FM…) no se automatiza.
- Reproducir: con el transporte en marcha y el modo encendido, el valor del carril pone el valor (y sale su CC); si no hay automatización en ese paso, no pasa nada.
- **Los carriles son los mismos que los de las macros de stock de esa pista**: un patrón con automatización de macros grabada en stock se leerá aquí como TUNE, REL, etc. Usa patrones limpios para probar.
- El carril 0 = TUNE queda reservado para el «step-drummer» futuro.

## Pruebas en el aparato (en este orden)
1. **Arranca y Master FX responde** (como SC24; la RAM no cambia).
2. **Pad 27**: MIDI 1, vista Preset: tres pulsaciones (línea, oscilador, apagado): al apagar, los pads 1-8 vuelven a ser las plantillas (el elegido encendido).
3. **Salida** (con un monitor MIDI en el USB o el DIN): con el modo encendido, gira K5 → CC 74 en el canal de la pista; K1 → CC 73; K7 → los tres mensajes del NRPN 0:76. Con **CC Tx** apagado en el Setup no debe salir nada.
4. **Reenvío interno** (SC05): pon el canal de MIDI 1 igual al de Synth 1; gira K5 → el CC 74 mueve el filtro del Synth 1 (y el nuestro).
5. **Entrada**: desde el DAW manda CC 74 / 71 / 73 por el canal de la pista con el modo encendido → los valores cambian (los LEDs de los knobs y el sonido). Con el modo apagado no pasa nada.
6. **Automatización**: pista MIDI 1 con el modo encendido, el patrón vacío; Record + Play, mueve K5 (filtro) durante un compás, para; reproduce: el filtro se mueve solo y el monitor muestra el CC 74 siguiendo el movimiento. Lo mismo con TUNE (página OSC1, K1).
7. **Lo que más importa vigilar**: con el modo encendido y **un patrón sin automatización**, reproducir **no debe mover ningún valor** por sí solo. Si se mueven (por ejemplo a 0 al arrancar el secuenciador), dímelo: sería que el stock llama a ese emisor con las posiciones guardadas de las macros, y SC25.1 lo filtra.
8. Un movimiento de knob mientras el secuenciador reproduce la automatización del mismo valor: gana la automatización en el siguiente paso, como en stock.

## Cómo está hecho (resumen; detalle en `docs/NOTAS.md`)
- **Salida**: `c_vsync` (después de marcar el valor sucio en el manejador de knobs) = `c_vcc_emit` (tabla `CC_TAB`; el emisor de CC de las plantillas `0x0804A356`, que SC05 sustituyó) + `c_vcc_rec` (la puerta de automatización `0x0802E62C(gate 0x2003C168, id, valor)`). Canal = `[[0x20011334 + 0xC] + 2 + pista]`.
- **Reproducción**: gancho de 4 bytes en la cabeza del emisor de macros de stock `0x080313C4` (`c_vplay`; el secuenciador lo llama con el valor del carril): transporte en marcha (`0x20011034`), emisor = MIDI 1 / MIDI 2 (`G + 0x110 / 0x158`, `G = [0x20039744]`), modo encendido y knob 0-7 → `c_vapply`; si no, el cuerpo de stock.
- **Entrada**: gancho de 4 bytes en la sección de CC de la función de MIDI de entrada `0x08051834` (`c_vmin` → `c_vin`): estado de los CC 99 / 98 en el registro de los canales «otros» del despachador de stock (`[[ctx + 0x10] + 15]`), búsqueda inversa en `CC_TAB`, `c_vstore` (valor, bit sucio / cursor de barrido; sin guardar ajustes ni enviar MIDI).
- Imagen de 0x60150 bytes (SC24: 0x5FDBC). La DSP no cambia.

## Pruebas de emulación
`emu_sc25.py` (los dos ganchos, el pad 27, los CC y NRPN de salida de varias páginas y de la segunda pista, los ids de los carriles, Clear, la reproducción con el transporte parado / en marcha, el emisor real de stock de MIDI 2, la entrada de CC / NRPN con todos los casos que se ignoran, el reenvío interno, el buzón del DSP) y las de SC23.x / SC24 sobre esta imagen.

## Si algo falla
Flashea SC24 (o SC23.6). Para volver al firmware original: el instalador, «RESTAURAR», o Novation Components.
