# SC28 — SC27 + MIDI (NRPN) para los parámetros extra de drums y para Master FX

`circuittracks-4486-SC28.syx` — SHA-256 en `manifest.json` (`syx_sha256`)
Marca `SC28`. Reserva: **SC27**. Todo probado en emulación; **nada probado en el aparato**.
RAM: **sin cambios**. DSP: sin cambios. Estado guardado: sin cambios.

## Qué añade
Los parámetros que nuestros parches añadieron a los drums y los de Master FX no tenían MIDI. Ahora **salen** al girar el knob y **entran** desde fuera, como **NRPN con valor de 7 bits** (CC 99 = MSB, CC 98 = LSB, CC 6 = valor).

### Drums — canal de drums (10 por defecto)
**NRPN MSB = 5, 6, 7, 8 → Drum 1, 2, 3, 4.** LSB = el parámetro:

| LSB | Parámetro | Knob | Valor |
|---|---|---|---|
| 1 | Envolvente de pitch (cantidad) | Shift + K1 | 0-127, **64 = centro** |
| 2 | Ring mod: frecuencia | K2 | 0-127 |
| 3 | LFO: cantidad | K7 | 0-127, 64 = centro |
| 4 | LFO: velocidad | Shift + K7 | 0-127, 64 = centro |
| 5 | Envolvente → corte del filtro | K4 | 0-127, 64 = centro |
| 6 | Resonancia | K6 | 0-127 |
| 7 | Forma de la envolvente | Shift + K4 | 0-127, 64 = centro |
| 8 | Ring mod: cantidad | Shift + K2 | 0-127 |
| 9 | Modo de filtro | Shift + K5 | 0-4 (DJ, paso banda, notch, comb, EQ tilt) |
| 10 | Punto de inicio (K3 a la izquierda de 0) | K3 | 0-15 |
| 11 | Bitcrush (K8 a la izquierda de 0) | K8 | 0-15 |
| 12 | Tipo de distorsión | Shift + K8 | 0-3 |

Los parámetros de stock de los drums (pitch, decay, distorsión, EQ…) siguen con sus CC de siempre.

### Master FX — canal 16
**NRPN MSB = 9**, LSB = `4 × conjunto + knob` (knob 0-3 = K1-K4), valor 0-127:

| Conjunto | Efecto (pad de Master FX) | LSB |
|---|---|---|
| 0 | Gate (pad 1) | 0-3 |
| 1 | Filtro (pads 2 y 3: comparten parámetros) | 4-7 |
| 2 | Digitise (pad 4) | 8-11 |
| 3 | Phaser (pad 5) | 12-15 |
| 4 | Vinyl (pad 6) | 16-19 |

### Reglas
- Sale con el filtro **CC Tx** del menú Setup; entra con **CC Rx**.
- Clear + knob también manda el valor por defecto.
- El aparato de stock ignora esos números (comprobado en emulación: no escribe ningún parámetro): no chocan con nada.
- No se graban en el secuenciador (no hay carriles para ellos): es control en vivo / desde un DAW.

## Pruebas en el aparato (con un monitor MIDI y, si puedes, un DAW)
1. **Arranca.** Todo lo de SC27 sigue igual.
2. Drum 1, gira **K2** (ring mod): el monitor muestra en el canal 10 `CC 99 = 5`, `CC 98 = 2`, `CC 6 = valor`.
3. Shift + K5 (modo de filtro): `99 = 5, 98 = 9, 6 = 0…4`. Shift + K8: `98 = 12`. K8 hacia la izquierda de 0: `98 = 11`. K3 hacia la izquierda de 0: `98 = 10`.
4. Drum 3: el MSB es 7.
5. K1 (pitch de stock): **no** manda NRPN (manda su CC de stock).
6. Desde el DAW, manda `99 = 5, 98 = 6, 6 = 100` al canal 10: la resonancia del Drum 1 sube (se oye y el LED de K6 lo refleja).
7. Master FX (Mixer → Mixer), pad 1, gira K1: canal 16, `99 = 9, 98 = 0, 6 = valor`. Pad 5 (Phaser), K2: `98 = 13`.
8. Desde el DAW, `99 = 9, 98 = 12, 6 = 127` al canal 16: el parámetro 1 del Phaser cambia.
9. Setup: CC Tx apagado → no sale nada; CC Rx apagado → no entra nada.
10. **Lo que hay que vigilar:** que al mover knobs de drums o de Master FX no haya tirones ni cuelgues (son tres mensajes MIDI por paso del knob; el envío es el mismo que el de los knobs del modo VCA-VCF de SC25, que ya probaste).

## Limitaciones conocidas
- Si el canal de drums se cambia en Setup, los NRPN de drums van por el canal nuevo (se usa la tabla de canales de stock). Master FX es siempre el canal 16.
- Los huecos (slots) de Master FX no tienen MIDI propio: al cargar un hueco los parámetros cambian sin mandar NRPN.
- Tres mensajes por cada cambio: con giros muy rápidos el tráfico MIDI es alto.

## Cómo está hecho (resumen; detalle en `docs/NOTAS.md`)
- Módulo nuevo `tools/nrpn28.py` (no toca `persist19` ni `build_sc17`); builder `tools/build_sc28.py`.
- Salida: dos envoltorios delante de los manejadores de knobs (`c_ndknob`: ranura 4 de los manejadores de macros de drums; `c_ngknob`: ranura 4 de la vista Mixer / Master FX): copian los valores a la pila, llaman al manejador de siempre y mandan lo que cambió por el helper de CC de las plantillas (el de SC05).
- Entrada: `c_nmin` delante de la cueva de `vcf21` en la sección de CC de la función MIDI-in de stock (`0x08051834`). El estado de selección NRPN es el registro de stock (`this + 5 × índice`, índice 2 = drums, 3 = resto); el manejador de stock ignora todo NRPN en el canal de drums y los MSB > 2 en los demás.
- Imagen de 0x61104 bytes.

## Pruebas de emulación
`emu_sc28.py` (instalación; salida de cada knob nuestro de drums con su valor en el cable, valores extendidos, modo de filtro, tipo de distorsión, Clear; entrada de los 12 LSB con sus topes y los bits vecinos intactos; números fuera de rango, otro canal, CC Rx apagado, copia interna: nada; Master FX ida y vuelta; el manejador de stock no escribe nada para esos números y sigue recibiendo los suyos) y las de SC23.x … SC27 sobre esta imagen.

## Si algo falla
Flashea SC27. Para volver al firmware original: el instalador, «RESTAURAR», o Novation Components.
