# S514D (diagnóstico) = SC51.4 + el mapa de memoria

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/s514d/circuittracks-4486-S514D.syx` | `552cd17922068accb19dff0a85fec1fada5b67c2ff056680ae46f717b2164f0b` | `S514D` |

Para saber el presupuesto de memoria que queda sin adivinar.

- **Núcleo 1 del DSP** (ni el ARM ni el núcleo 0 pueden leerlo): al arrancar apunta su OMR y si 16 direcciones de P, de X y de Y guardan un valor (escribe y lo devuelve en seguida); después, en sus pasadas libres, la suma de cada bloque de 64 palabras de su X ($0000-$5FFF) y su Y ($0000-$3FFF): qué bloques cambian y cuáles son ceros. Lo deja en la memoria externa (`Y:$57C000`).
- **Núcleo 0 del DSP:** el PC lee su X y su Y enteras dos veces (al empezar y al terminar) y compara.
- **RAM del ARM:** el PC escribe centinelas en los tramos que creemos libres y al final mira cuáles siguen intactos (también dice cuánto baja la pila).
- **Save** = el tiempo del núcleo 0 (como S484D). **Sin el Glitch ni el gesto mecánico** (pads 6 y 31 de Master FX): su sitio en el núcleo 1 lo usa la prueba.

## Cómo
1. Instalar S514D. Conectar por USB a este PC y cerrar Components, el uploader, la app de la tarjeta y cualquier DAW. Avisar a Claude.
2. Claude: `python tools/memmap.py start` (unos minutos: lee el núcleo 0 entero y pone los centinelas).
3. Usar el aparato **10-15 minutos sin apagarlo**, todo lo posible: patrones y escenas, cambiar de proyecto y de pack, Save, Sample Rec y el sample capturado, MIDI 1 / 2 con FM poly y con el granular, Synth 1 / 2 con acordes, Master FX, Mixer, la app de la tarjeta por USB si se quiere. Avisar a Claude.
4. Claude: `python tools/memmap.py end` (el mapa).
5. Instalar S514D2 y repetir, o volver a instalar la Beta 5.17.

## Verificación en emulación
- `emu_s514d.py`: `rfill` / `rchk` (centinelas, dos cambiados detectados, rangos rechazados: sin alinear, fuera de la RAM, vacío, junto a la pila); el informe del núcleo 1 (marca, OMR, 48 pruebas, pasadas, un bloque que cambia contado, uno constante no, uno a cero); S514D2 lo mismo y el stub antes del programa del núcleo 1.
