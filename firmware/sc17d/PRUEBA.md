# SC17D — diagnóstico de la vista Master FX

`circuittracks-4486-SC17D.syx` — SHA-256 `3a82a33347fd67d7ab18a698a07c763d4eea6bc6bf519a80c22ae7ab59959705`
Imagen de 0x5902c bytes, CRC 0xc3f55d6a, marca `SC17D`.

Es **SC17.2** (Master FX en Shift + Mixer, entrada de línea v2) con un panel de diagnóstico en los LEDs. Sirve para saber en qué paso se pierde Master FX en el aparato. No cambia nada más.

## Cómo leerlo
Abre la vista **Preset del Synth 1** (o del Synth 2) y **mantén Shift**. Los pads 25–29 siguen mostrando el modo de entrada de línea. Las filas 2 y 3 pasan a mostrar el diagnóstico: **brillante = 1 / sí**, **tenue = no**.

**Fila 2 (pads 9–16): número binario** = bytes de RAM libres en el heap ÷ 16. Pad 9 vale 128, pad 10 vale 64, … pad 16 vale 1.

**Fila 3:**

| Pad | Significa |
|---|---|
| 17 | El bloque de memoria de Master FX está disponible |
| 18 | Modo Master FX activado ahora mismo |
| 19 | Shift + Mixer llegó al código de SC17 (se queda encendido hasta apagar) |
| 20 | Mixer sin Shift llegó al código de SC17 (se queda encendido) |
| 21 | Al pulsar pads en el Mixer se llamó a mi código (se queda encendido) |
| 22 | Al pintar LEDs del Mixer se llamó a mi código (se queda encendido) |
| 23 | La comprobación "Master FX visible" dio sí alguna vez (se queda encendido) |
| 24 | La reserva de memoria de SC14–SC17 está activa |

## Prueba (en este orden, sin apagar entre pasos)
1. Envía SC17D y arranca.
2. **Synth 1 → Preset, mantén Shift.** Anota qué pads de las filas 2 y 3 están brillantes (una foto vale).
3. Pulsa **Mixer**, pulsa un par de pads del Mixer.
4. Vuelve a **Preset del Synth 1, mantén Shift**, anota / foto.
5. Pulsa **Shift + Mixer**, luego pulsa el pad 1 y gira un knob.
6. Vuelve a **Preset del Synth 1, mantén Shift**, anota / foto.

En emulación, al final del paso 6 se encienden 17–24 y la fila 2 muestra 15 (pads 13–16).

## Volver atrás
Envía SC17.2, SC17.1 o SC16.1.
