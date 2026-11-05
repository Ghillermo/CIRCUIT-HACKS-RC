# Beta 5.17 = Beta 5.16 + más voces FM (en el otro núcleo del DSP)

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/b5.17/circuittracks-4486-B5.17.syx` | `2f755a22d0b7db1f3123ddf8de2ef3c54544ccf524f824b5fc246b2d189ab688` | `B5.17` |

Es SC51.4 con la marca de la beta.

**Qué cambia:** las voces FM del sinte propio de MIDI 1 / 2 las calcula el núcleo 1 del DSP (el que lleva el granular y el Glitch), no el núcleo 0. **6 voces por pista también con MIDI 1 y MIDI 2 en FM poly** (antes 3 + 3), y el núcleo 0 queda libre del bucle FM (menos traqueteo con el resto sonando). Si el núcleo 1 no llega a tiempo (en S513D: unas 10 voces FM, unas 8 con el granular), el límite de voces apaga una voz FM. El FM suena 1,3 ms más tarde que el resto, como el granular. Si el aparato no arranca: Scales + Preset + Note e instalar la Beta 5.16.

## Qué probar
1. **El sonido FM igual que antes:** patches FM conocidos (pad 24 de la fila de motores), mono y poly: mismo timbre, mismas envolventes; los sonidos de partida (pad 8 mantenido).
2. **Ataques:** notas cortas y percusivas (bombo, campanas) sin clic ni la cola de la nota anterior al empezar.
3. **Más voces:** MIDI 1 y MIDI 2 en FM poly a la vez, acordes de 6 en cada uno (12 notas): todas suenan mientras el DSP llega; con releases largos el límite apaga las más bajas, sin traqueteo.
4. **Con el granular** en una pista y FM poly en la otra: acordes de 4-6; nada se cuelga ni se frena el tempo.
5. **El resto sin cambios:** Synth 1 / 2, drums, Master FX, el Glitch (pad 6 de Master FX), el sample capturado.

## Verificación en emulación
- `emu_fmc1_core1.py`: el núcleo 1 (2 038 de 2 048 palabras, con el Glitch): los estados y las muestras de una voz = el bucle FM del núcleo 0 bit a bit (la carga de S513D como referencia); una voz de pista a su sitio; una ranura callada no se toca; los bloques en su búfer; con pocas pasadas, tarde.
- `emu_fmc1_core0.py`: el núcleo 0 de la imagen copia la ranura (incremento, sello, cuenta de reinicios, parámetros), marca los estados, y toma las muestras del núcleo 1 a partir del tercer bloque (ceros antes).
- `emu_poly3.py`: 6 voces FM por pista con las dos en FM poly, ranuras 6 t + v en X:$4000.
- `emu_vguard.py`: todo lo de antes y un bloque tarde del núcleo 1 = una voz apagada.
- `emu_fmspi.py`: las mismas escrituras al DSP que SC51.3.
