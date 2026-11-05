# S514D2 (diagnóstico) = SC51.4 + el mapa de memoria (núcleo 1 en MS = 1)

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/s514d2/circuittracks-4486-S514D2.syx` | `68a5aa62b86155374640ebe21f4fa607a55be8071686572b7b53cd0a1111877a` | `S514D2` |

Para saber el presupuesto de memoria que queda sin adivinar con el **núcleo 1 arrancado con MS = 1** (el mismo stub que el aparato manda al núcleo 0: `tools/c1ms.py`). La pregunta: ¿tiene entonces el núcleo 1 más memoria de programa (4 K, 16 K…) y siguen funcionando su servicio de lecturas, el granular y las voces FM? Si el aparato no arranca o no suena: Scales + Preset + Note e instalar la Beta 5.17 o S514D.

- **Núcleo 1 del DSP** (ni el ARM ni el núcleo 0 pueden leerlo): al arrancar apunta su OMR y si 16 direcciones de P, de X y de Y guardan un valor (escribe y lo devuelve en seguida); después, en sus pasadas libres, la suma de cada bloque de 64 palabras de su X ($0000-$5FFF) y su Y ($0000-$3FFF): qué bloques cambian y cuáles son ceros. Lo deja en la memoria externa (`Y:$57C000`).
- **Núcleo 0 del DSP:** el PC lee su X y su Y enteras dos veces (al empezar y al terminar) y compara.
- **RAM del ARM:** el PC escribe centinelas en los tramos que creemos libres y al final mira cuáles siguen intactos (también dice cuánto baja la pila).
- **Save** = el tiempo del núcleo 0 (como S484D). **Sin el Glitch ni el gesto mecánico** (pads 6 y 31 de Master FX): su sitio en el núcleo 1 lo usa la prueba.

## Cómo
1. Instalar S514D2. Conectar por USB a este PC y cerrar Components, el uploader, la app de la tarjeta y cualquier DAW. Avisar a Claude.
2. Claude: `python tools/memmap.py start` (unos minutos: lee el núcleo 0 entero y pone los centinelas).
3. Usar el aparato **10-15 minutos sin apagarlo**, todo lo posible: patrones y escenas, cambiar de proyecto y de pack, Save, Sample Rec y el sample capturado, MIDI 1 / 2 con FM poly y con el granular, Synth 1 / 2 con acordes, Master FX, Mixer, la app de la tarjeta por USB si se quiere. Avisar a Claude.
4. Claude: `python tools/memmap.py end` (el mapa).
5. Volver a instalar la Beta 5.17.

## Verificación en emulación
- `emu_s514d.py`: `rfill` / `rchk` (centinelas, dos cambiados detectados, rangos rechazados: sin alinear, fuera de la RAM, vacío, junto a la pila); el informe del núcleo 1 (marca, OMR, 48 pruebas, pasadas, un bloque que cambia contado, uno constante no, uno a cero); con S514D2, la llamada del programa del núcleo 1 pasa por `c_c1ms`, que manda antes el stub.
