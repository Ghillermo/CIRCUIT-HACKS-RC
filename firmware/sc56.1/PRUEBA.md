# SC56.1 = SC56 + el oscilador del sinte propio sin calcular las ondas a peso 0

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/sc56.1/circuittracks-4486-SC56.1.syx` | `47d872ffdd1e4d87bda7c6d0cb3f4952236b4db810abcacbb26b6f477e827ccf` | `SC56.1` |

**Lo nuevo** (el usuario, 2026-11-10: «build 1 and then 2», el punto 2: la CPU), `vcf21_dsp.use_wskip()`:
- El oscilador del sinte propio de MIDI 1 / 2 calculaba **las cuatro ondas en cada muestra** (seno, triángulo, las siete sierras de la
  supersaw con sus comprobaciones de BLEP, el pulso con las suyas) y las mezclaba con los pesos del morph (WAVE), de los que como mucho dos no
  son 0. Ahora cada onda mira su peso y **se salta a 0**. El sonido es el mismo **bit a bit**; las seis sierras desafinadas de la supersaw solo
  se quedan quietas mientras su peso es 0 (giran libres: no se oye).
- **Medido en el núcleo 0 emulado** (instrucciones por bloque y voz, contra SC56): seno −62 %, triángulo −48 %, sierra / supersaw / pulso
  −22 / −23 %, dos osciladores −21 a −43 %. Más voces o más efectos antes de que el DSP se quede sin tiempo (y el limitador de voces actúa
  más tarde).
- Coste: 13 palabras del núcleo 0 (hasta `P:$3F26`; las tablas en `$3F4E`: quedan 40). Imagen `0x6FE2C` (468 B libres al final; 7 446 B en
  total).
- **Lo que se midió y se dejó (de la lista):** el «latido» del motor propio (cada 8 ms) es también el único camino de los códigos 27..34
  (OSC 2 y los valores con Shift): espaciarlo haría lentos esos knobs; el dibujo de la vista Patterns con listas mutadas son unos miles de
  instrucciones por fotograma, solo en esa vista: no vale el sitio.

## Qué probar
1. El sinte propio con el oscilador (pad 27): mueve WAVE (K3 de OSC 1) de seno a cuadrada y vuelta; ¿suena igual que en la Beta 5.44 / 5.45?
2. Supersaw (sierra, SHAPE a la derecha) y dos osciladores (FM, sync, ring): igual que antes.
3. Poly con 4+ notas por pista en sierra: ¿aguanta más antes de que el DSP corte voces?

## Verificación en emulación
- `emu_wskip_dsp.py` SC56.1 / SC56: 12 casos (posiciones puras y mezclas de WAVE, supersaw, seno doblado, dos osciladores con FM y sync)
  **bit a bit** iguales; el coste de cada uno.
- `verify_builds.py`: las anteriores sin cambios.
