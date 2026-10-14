# SC40.7 — patches propios entre packs y tabla nueva de dinámicas

`circuittracks-4486-SC40.7.syx` — SHA-256 `720c760aa4999b1db2de5b23fc059467e9c5884bcb8e6d593d02cbf7d708ffe4`
Imagen de 0x69a68 bytes, CRC 0x1db51b68, marca `SC40.7`.

Es SC40.6 (cadenas de patrones, ver `firmware/sc40.6/PRUEBA.md`) con dos cosas más. **Escribe en la SD** (la copia de patches): no es para las versiones S.

## 1. Patches del sinte propio de MIDI 1 / 2, de un pack a otro
El mismo lenguaje que con los samples y los patches de sinte:
1. Vista Preset de MIDI 1 o MIDI 2, pack de origen cargado: **Duplicate + hueco A** (parpadea). Ese patch queda recordado.
2. Carga el otro pack y vuelve a la vista Preset de MIDI 1 / 2: **el botón Duplicate está en amarillo** (hay un patch de otro pack esperando).
3. **Duplicate + hueco B**: el patch de A (motor, parámetros y nombre) se escribe en B. Puedes pegarlo en varios huecos.

Dentro del mismo pack Duplicate + A + B sigue intercambiando los dos, como antes. No se copia si A está vacío o si el banco de B no existe en ese pack (un pack con menos de 8 patches de sinte por banco).

## 2. Dinámicas (fila 3 del modo del pad 25 de Pattern Settings)

| Pad | M (micropasos: posición y duración) | V (velocity) | |
|---|---|---|---|
| 1 | — | — | sin modificación |
| 2 | −2 a +2 | — | drunk |
| 3 | −2 a +2 | 0 a +32 | drunk y acentos |
| 4 | — | 0 a +32 | acentos |
| 5 | −1 a +3 | 0 a +32 | arrastre y acentos |
| 6 | −1 a +3 | — | arrastre |
| 7 | — | −32 a +32 | dinámica equilibrada |
| 8 | — | −32 a +64 | dinámica de acentos |

## Qué probar
1. Guarda un patch propio en un hueco del pack A (Clear + pad dos veces). Duplicate + ese hueco. Carga el pack B, MIDI 1, Preset: Duplicate amarillo. Duplicate + un hueco: aparece ocupado; tócalo: suena el patch.
2. Vuelve al pack A: el hueco original sigue ahí.
3. Duplicate + A + B dentro de un pack: intercambio, como antes.
4. Cada pad de dinámicas con un patrón sencillo: 2 y 6 mueven la nota y su duración; 4, 7 y 8 solo la velocity; 3 y 5 las dos cosas.
5. Lo de SC40.6 y SC40.4 igual.

## Verificación en emulación
- `emu_sc40_7.py` (tarjeta modelada, dos packs): la marca queda en la palabra del DSP; en el otro pack, una lectura de 64 B del banco del pack de origen por su número, la tarea de almacenamiento devuelta al pack cargado, una escritura de 64 B en el hueco destino; los patches de sinte de los dos packs y el hueco de origen intactos; cerrojo del búfer liberado; nada escrito si el banco no existe, si el hueco recordado está vacío o con una pulsación normal.
- `emu_sc40_3.py` (elige la tabla por la imagen), `emu_sc40_5.py` y `emu_sc39_4.py` (intercambio dentro del pack) sobre SC40.7.
- **Sin comprobar en emulación:** la tarjeta real.
