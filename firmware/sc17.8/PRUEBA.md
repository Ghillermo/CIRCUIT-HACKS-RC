# SC17.8 — modos otra vez en Shift + Preset, pad 8 de «apagar todo» y toque para desactivar en Master FX

`circuittracks-4486-SC17.8.syx` — SHA-256 `869848d461260786e713f526e30cc9256a5bcfe883312c55c03b49114ea22e3b`
Imagen de 0x598b8 bytes, CRC 0xcdf7a4eb, marca `SC17.8`.

Es **SC17.7** (la que ya probaste: el song pointer funciona) con tres cambios. La reserva de RAM no crece: sigue en 220 bytes (unos 20 de margen).

## 1. Los modos de la fuente del sinte vuelven a Shift + Preset
La vista Shift + Scales de SC17.7 no se mostraba, así que se deshace: **los modos son los de SC17.5 / SC17.6.**
- Vista **Preset** de un sinte (Synth 1 o Synth 2), **mantén Shift** y pulsa los pads 25–31 (fila inferior):

| Pad | Modo |
|---|---|
| 25 | Noise (stock) |
| 26 | Entrada 1 |
| 27 | Entrada 2 |
| 28 | Entrada 1 (el otro signo) |
| 29 | Entrada 2 (el otro signo) |
| 30 | **Retorno del delay** |
| 31 | **Retorno de la reverb** |

- La vista **Shift + Scales** vuelve a ser la de stock (con SC17.7 se sustituyó el selector; ahora no hay nada nuestro en ella).
- Sigue el nivel ×16 de los retornos de SC17.7 (`linein3.FX_GAIN_SHIFT = 3`). Si saturan o se oyen bajos, dímelo.
- No se guarda: al encender, Noise.

## 2. Master FX: pad 8 = apagar todo lo que esté retenido con Shift
En la vista Master FX (Mixer → Mixer), **el último pad de la fila 1 (pad 8)** desactiva a la vez todos los efectos activados con **Shift + pad**:
- los de la fila 1 (Gater, Auto-Filter LP/HP, Digitise, Phaser, Vinyl),
- los huecos asignados de la fila inferior,
- y los efectos originales de la fila inferior (Gater 1/4–1/32, Auto-Filter).
- **No** toca lo que se está **manteniendo pulsado** (eso se suelta solo), **ni** el song pointer (su inicio fijo se quita con Shift + el mismo paso), **ni** las asignaciones de los huecos.
- LED: encendido mientras haya algo retenido, tenue si no. Color provisional (el del pad «FX off» de stock): dime si prefieres otro.

## 3. Tocar un pad activado lo desactiva
Un efecto retenido (Shift + pad) se apaga con **un solo toque** al pad, **sin Shift**. Vale para:
- la fila 1 de Master FX,
- los huecos asignados de la fila inferior,
- los efectos originales de la fila inferior (en la vista Master FX **y también en la vista FX**, que usa los mismos pads).

Detalles:
- El toque que apaga **no** deja el efecto «mantenido»: se apaga al tocar, no al soltar.
- Si había dos Gaters (o dos Auto-Filter) retenidos y apagas el activo, el otro retoma el control.
- Un pad no retenido se sigue comportando igual: mantener = activo mientras lo mantienes, Shift + pad = retener.
- Shift + pad sigue conmutando el retenido (encendido / apagado) como antes.
- El gesto «mantener un efecto de arriba + pulsar uno de abajo» para asignar sigue igual (si el de arriba estaba retenido, ese primer toque lo apaga, pero el mantener y la asignación funcionan).

## Cómo está hecho
- `build_sc17.use_clearpad()` (`tools/build_sc17.py`), sin RAM nueva: solo usa los bits de retención que ya existen (`S_LATCH` del bloque de Master FX = fila 1 y huecos; `S_LATCH` del estado de SC14 = efectos originales de la fila inferior).
  - `c_gpress` (fila 1) y `c_f_press` (huecos y fila inferior, también en la vista FX): sin Shift, si el bit está retenido lo borra en lugar de marcar «mantenido». En los efectos de SC14 se vuelve a elegir el Gater / Auto-Filter activo con la rutina `c_gpick_t` de SC14.
  - `c_clrall` (pad 8): pone a 0 ambos bytes de retención y recalcula el Gater y el Auto-Filter activos de SC14, de modo que el siguiente ciclo del servicio DSP devuelve la ganancia y el filtro máster de stock.
  - `c_clrled`: LED del pad 8.
- Los modos del sinte son los de SC15 (`c_spad` / `c_sleds` en la vista Preset). `modeview.py` ya no se usa en este build.
- Builder: `tools/build_sc17_8.py`.

## Verificación en emulación
- `emu_sc17_8.py`:
  - la vista Preset del sinte tiene los manejadores de SC15 y la vista Shift + Scales es la de stock;
  - pad 8: apaga los de la fila 1, los de SC14, los huecos asignados y deja intactos lo mantenido, el song pointer y las asignaciones; el DSP recibe el apagado (FX_ON = 0, ganancia y filtro máster de stock); en el Mixer normal es el mute de stock; LED encendido / tenue;
  - toque para apagar: fila 1, efectos de SC14 (incluido el relevo entre dos Gaters), huecos asignados, y en la vista FX; el pad 25 («FX off») sigue siendo el de stock.
- `emu_sc17.py`, `emu_sc17_5.py` (incluye las pruebas de modos en Preset), `emu_sc17_6.py`, `emu_sc17_7.py` (song pointer), `emu_sc17_core.py`, `emu_sc17_5_dsp.py` y `verify_builds.py`: pasan; todos los builds anteriores se siguen generando idénticos.

## Pruebas en el aparato
1. Envía SC17.8. Comprueba que arranca y que todo lo de SC17.7 sigue (song pointer, Master FX, FX).
2. **Modos:** vista Preset del Synth 1, mantén Shift y pulsa el pad 30 con un patch con noise al máximo y algo enviado al delay. Debe oírse. Prueba también el pad 26–29 (entradas) y el 31.
3. **Pad 8:** en Master FX, retén (Shift + pad) varios efectos de arriba y de abajo → pulsa el pad 8: todos se apagan; el LED del pad pasa de brillante a tenue.
4. **Toque:** retén un efecto → tócalo una vez sin Shift: se apaga. Repite con los de la fila inferior (en Master FX y en FX).
5. Si algo no cuadra (p. ej. quieres que el toque solo valga en Master FX, o que el pad 8 apague también el song pointer), dímelo.

## Volver atrás
Envía SC17.7 o SC17.6 (SC17.6 es la última con la vista de modos en Preset y sin song pointer).
