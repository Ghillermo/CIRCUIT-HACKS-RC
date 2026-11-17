# Beta 5.59 = SC57.4 con la marca de la beta

| Fichero | SHA-256 del `.syx` | Marca |
|---|---|---|
| `firmware/b5.59/circuittracks-4486-B5.59.syx` | `459440657939377c3d5d22a7e8d80e0e9f09c867a7f20d9d2980325bd30299bf` | `B5.59` |

**Lo nuevo** (sin probar en el aparato):
- **Cadenas de grupos de patrones** (sustituyen a las reglas por patrón): cada pista toca **A × i → B × j → C × k** y vuelve a A; A, B y C son tramos de patrones seguidos; i, j, k de 1 a 16. Sin B = solo A; sin C = A, B. Cada escena guarda la cadena de cada pista.
- Todo lo de la Beta 5.58 (carriles extra, destinos con Duplicate + knob, sin los 48 instrumentos FM): ver `firmware/b5.58/PRUEBA.md`.

## Qué probar
1. Vista Patterns, **Shift + Octave ▲** (modo cadena).
2. Synth 1: **Shift + patrón 1**, **Shift + patrón 2** → A = 1-2 (el 1 en amarillo). **Shift + patrón 4**, **Shift + patrón 4** → B = 4 (verde). **Shift + patrón 6**, **Shift + patrón 7** → C = 6-7 (rojo). Tras el primer Shift + pad, ese pad se ve blanco hasta el segundo.
3. Toca el pad amarillo (patrón 1) y gira **K1** a la derecha: los LEDs de los knobs cuentan las repeticiones de A; pasa de 8 y los primeros se ponen azules (10 = dos azules y seis blancos). Deja A en 2.
4. Play: suena 1 2 1 2 4 6 7 1 2 1 2 4 6 7…
5. Borra C (Clear + pad rojo): 1 2 1 2 4 1 2… Borra B: solo 1 2.
6. Duplicate + pad amarillo de Synth 1, luego un pad de Synth 2: Synth 2 con la misma cadena. Clear + pad amarillo de Synth 1: la de Synth 2 se queda.
7. Escenas: con cadenas distintas guarda la escena 1 (Mixer, Shift + escena 1); cámbialas y guarda la 2. Elige cada una (parado o encadenándolas sonando): cada escena con sus cadenas; una pista sin cadena en la escena, con su cadena de stock.
8. Una escena con varias pistas: cambia de escena al acabar la cadena más larga.
9. Guarda el proyecto, apaga, enciende, cárgalo: las cadenas siguen.
10. Un proyecto anterior con reglas por patrón: suena con sus cadenas de stock (las reglas antiguas no se usan).

## Verificación en emulación
- `emu_pgroups.py` (28 / 28): el motor contra un modelo (con y sin B / C, 16 repeticiones, fuera del grupo, reinicio y previsión, sin cadena, modo apagado), los gestos por el controlador, los LEDs, K1, Clear, Duplicate, escenas parado y sonando, tarjeta.
- `emu_xlanes.py`, `emu_scnchain.py`, `emu_p4dup.py`, `emu_patmut.py`, `emu_autorel.py`, `emu_edlock.py`, `emu_sc44_3.py`, `emu_vorder.py`: igual que sobre la Beta 5.58.
