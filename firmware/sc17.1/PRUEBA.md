# SC17.1 — SC17 + entrada de línea v2 (+6 dB y fase invertida)

`circuittracks-4486-SC17.1.syx` — SHA-256 `d62ea204fa0b2ebb1e22d26ef500e730526f37ae477f184f3cb827b5e9982b0c`
Imagen de 0x58ee4 bytes, CRC 0x3d1d1099, marca `SC17.1`.

Es **SC17** con dos cambios en la entrada de línea del sinte (SC15):

1. **Nivel ×2 (+6 dB)** en los modos de entrada, con saturación (si la señal pasa de la mitad del fondo de escala, se recorta en lugar de dar la vuelta).
2. **Dos modos nuevos con la señal en fase invertida.**

## Uso
Vista **Preset** del Synth 1 o 2, manteniendo **Shift**, fila 4:

| Pad | Modo |
|---|---|
| 25 | Noise (stock) |
| 26 | Entrada 1 |
| 27 | Entrada 2 |
| **28** | **Entrada 1 invertida** |
| **29** | **Entrada 2 invertida** |

- Mientras mantienes Shift, los 5 pads muestran el modo: el elegido brillante y los demás tenues.
- Sin Shift, la vista Preset funciona como siempre. Shift + pad 30 o cualquier otro pad, también.
- No se guarda: al encender, Noise.
- **Observado en el aparato:** los pads 26 y 27 llevan la señal **invertida** y los pads 28 y 29 la señal **sin invertir** (al revés que en la tabla, que sigue el código). Pendiente de confirmar.
- **Limitación:** este modo no puede tomar el delay ni la reverb como entrada externa.

## Cómo está hecho
- **DSP:** P:$9C3 salta ahora a `l2_hook`, en la zona ampliada del programa (después del código de SC16/SC17).
  - En modo entrada, una vez por bloque y por sinte, se copian las 32 tramas del canal elegido a Y:$3A00 (Synth 1) o Y:$3A40 (Synth 2), multiplicadas por 2, y negadas en los modos 3 y 4, con saturación. La caché se identifica por y:$FFD y el modo.
  - La voz lee ese búfer en lugar de la tabla de ruido.
  - r4/m4 se guardan y se restauran en X:$3A07/$3A08.
  - En modo Noise, todo funciona exactamente como en stock.
- **ARM:** el mismo código de SC15 con 5 modos (pads 25–29).

## Verificación en emulación
- `emu_sc15.py` con 5 modos y ganancia 2, DSP con núcleo completo:
  - en los dos sintes, los modos 1/2 dan exactamente **2 × entrada × nivel de noise** y los modos 3/4 **−2 × entrada × nivel** (error 0);
  - en modo Noise, la mezcla es idéntica a stock;
  - el otro sinte no cambia;
  - pads, LEDs y envío de los modos, correctos.
- Regresiones de SC17 completas sin cambios. SC15, SC16 y SC17 se siguen generando idénticos.

## Pruebas en el aparato
1. Envía SC17.1 y comprueba que todo funciona como en SC17.
2. Synth 1, entrada 1 (pad 26): el nivel debe ser ~6 dB más alto que antes.
3. Pad 28: misma señal invertida. Prueba Synth 1 con pad 26 y Synth 2 con pad 28 sobre la misma entrada, con los mismos ajustes de patch: deberían cancelarse al sumarse.
4. Si la entrada satura con fuentes muy calientes, baja el nivel de la fuente o dímelo para usar menos ganancia.

## Volver atrás
Envía SC17 con el cargador.
