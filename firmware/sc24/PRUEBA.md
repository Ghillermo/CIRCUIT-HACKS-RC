# SC24 — SC23.6 + pad 27 de tres estados, páginas en los pads 1-8, segundo oscilador, interacciones, orden de la cadena y parafonía

`circuittracks-4486-SC24.syx` — SHA-256 en `manifest.json` (`syx_sha256`)
Marca `SC24`. Reserva: SC23.6 (confirmado por el usuario: «en líneas generales funciona»). Todo probado en emulación; **nada probado en el aparato**.

## ⚠️ Antes de nada: el margen de RAM
La reserva bajo el heap sube a **236 B** (SC23.6: 220 B) para guardar los valores del segundo oscilador. El heap del aparato termina en `0x20044D68` y la reserva empieza en `0x20044D6C`: **4 B de margen** (antes 20 B). Si al encender **Master FX, el modo VCA-VCF y el sidechain no responden** (todo lo de SC14+ se apaga a la vez), la reserva no cupo: flashea SC23.6 y dímelo. Es lo primero que hay que comprobar.

## Lo que cambia en la vista Preset de MIDI 1 / 2
| Pad | Función |
|---|---|
| **27** | Por pista: **apagado** (pad apagado) → **entrada de línea con VCA-VCF** (naranja) → **oscilador con VCA-VCF** (verde) → apagado. Apagado = los knobs son los macros de stock y no se pueden tocar los parámetros de OSC ni VCA-VCF. |
| **1-8 (primera fila)** | Con el pad 27 encendido: **selector de página** de los knobs. Pad 1 = VCA-VCF (naranja), pad 2 = OSC1 (verde), pad 3 = OSC2 (verde azulado, solo con dos osciladores). El elegido brilla, los otros tenues, el resto apagado. Con el pad 27 apagado, o mientras el editor de CC está abierto, son las plantillas de siempre. Siempre se empieza en VCA-VCF. |
| **28** | 1 o 2 osciladores (encendido = 2). Solo con el pad 27 encendido. |
| **29** | Orden de la cadena: apagado = VCA → FX → filtro (el de siempre); encendido (azul claro) = **filtro → VCA → FX**. Solo con el pad 27 encendido; vale para la entrada de línea y para el oscilador. |
| 25, 26 | Editor de CC y patch flip, como antes (el patch flip se apaga si enciendes el modo). |

## Páginas de knobs
- **Página 1 (VCA-VCF)**: como SC23.6.
- **Página 2 (OSC1)**: como antes, más **MIX** (Shift + K2, 0 = solo OSC1 … 127 = solo OSC2; empieza en 64) y **BITSYNC** (Shift + K3, knob lento con zonas: nada, Sync, xor, or, nor, and, nand; LED = color de la zona, brillo = posición dentro de la zona).
- **Página 3 (OSC2)**: **TUNE2** (K1), **SHAPE2** (K2), **WAVE2** (K7), **FINE2** (Shift + K1), **FM** (Shift + K2), **RING** (Shift + K3). La envolvente y el LFO a tono / forma / morph (K3-K6, K8, ENVM) **son los de OSC1 y valen para los dos** (no cabe una copia en RAM).

## El sonido
- **FM**: OSC2 modula la fase de OSC1 (portador). **Ring**: producto de los dos, mezclado con la mezcla normal. **Mezcla**: balance OSC1 / OSC2.
- **Zona Sync**: OSC1 es el maestro; OSC2 **invierte la dirección de su fase** (sync suave) en cada ciclo de OSC1. La posición dentro de la zona elige **cada cuántos ciclos** (1 … 8).
- **Zonas xor / or / nor / and / nand**: operación bit a bit de las dos señales de 24 bits; la posición es la cantidad (0 = sin efecto, 127 = solo el resultado bit a bit).
- **Parafonía** (con 2 osciladores): una nota = unísono (los dos tocan la misma, cada uno con su tono y fino); dos notas = OSC1 la primera, OSC2 la segunda; la tercera sustituye a la que lleva más tiempo, la cuarta a la otra. Al soltar una nota que suena, el oscilador pasa a la que sigue pulsada (unísono). **Las notas sustituidas no vuelven** al soltar (no cabe memoria para la pila). La envolvente se reinicia en cada nota nueva; la velocidad es la de la última nota. El seguimiento de la nota del filtro usa la **media** de las dos notas.

## Qué NO se guarda
Los valores de OSC2 (TUNE2, FINE2, WAVE2, SHAPE2), MIX, BITSYNC, FM, RING, y los pads 28 / 29 (orden y número de osciladores) **vuelven a su valor neutro al apagar el aparato**. El estado del pad 27 sí se guarda, como antes. (La RAM guardada está llena: ver `docs/NOTAS.md`.) Al instalar SC24 se descartan además los valores guardados de SC23.6 (cambia la firma).

## Pruebas en el aparato (en este orden)
1. **Arranca y Master FX responde** (ver el margen de RAM arriba).
2. MIDI 1, vista Preset: pad 27 una vez (naranja, la entrada de línea pasa por el VCA-VCF), dos (verde, oscilador), tres (apagado). Con el modo apagado los pads 28 / 29 no hacen nada y los pads 1-8 son plantillas.
3. Con el oscilador encendido: pads 1 / 2 / 3 (este solo con el pad 28 encendido) y los knobs de cada página; el LED del pad elegido brilla.
4. Pad 29: debe notarse el orden de la cadena (con FX duro y filtro cerrado, el nivel cambia mucho).
5. Dos osciladores: MIX, FM, Ring; zonas de BITSYNC; en Sync mueve TUNE2 y oye cómo el timbre sigue el tono de OSC1.
6. Parafonía: toca una nota (unísono, con FINE2 ≠ 0 se oye el batido), dos (acorde), tres.
7. **Si las notas vuelven a fallar**, dímelo con el patrón (la mayor parte del tráfico nuevo al DSP es un recorrido continuo de los 8 valores nuevos, un mensaje cada 2 ms).

## Pruebas de emulación
`emu_sc24.py` (pad 27, pads 28 / 29, la fila de páginas, los knobs de las páginas B y C, los valores volátiles, Clear, las notas parafónicas, y el recorrido completo: los mensajes del ARM reproducidos en el programa real del DSP), `emu_sc24_dsp.py` (buzón de 7 bits, ruta bit a bit contra SC23.6, oscilador doble con mezcla / ring / FM / bit a bit / sync, media de las notas, coste: +8,1k instrucciones por bloque con dos osciladores en las dos pistas), y las de SC23.5 / SC23.6 sobre esta imagen.
